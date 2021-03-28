from os import path, name
from sys import argv, stderr, exit
from socket import socket, SOL_SOCKET, SO_REUSEADDR
from pickle import dump, load
from time import process_time
from multiprocessing import Process, active_children, cpu_count
from sqlite3 import connect
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QFrame
from PyQt5.QtWidgets import QLabel, QGridLayout, QPushButton
from PyQt5.QtWidgets import QLineEdit, QTextEdit, QScrollArea
from PyQt5.QtWidgets import QSlider, QCheckBox, QRadioButton
from PyQt5.QtWidgets import QListWidget, QDesktopWidget
from PyQt5.QtCore import Qt
import argparse
import textwrap
from database_handler import create_sql_command

# If not running on MS Windows, then import some signal-related names.
if name != 'nt':
    from signal import signal, SIGCHLD


# If not running on MS Windows, then define joinChildren.  The main
# function installs it as the handler for SIGCHLD signals.
if name != 'nt':
    def joinChildren(signal, stackFrame):
        # Wait for / reap all children that have exited.
        active_children()


def consumeCpuTime(delay):
    i = 0
    initialTime = process_time()
    while (process_time() - initialTime) < delay:
        i += 1  # Do a nonsensical computation.


# determine whether to call handleOverviews or handleDetails
def handler(sock, cursor, delay):
    in_flow = sock.makefile(mode="rb")
    package = load(in_flow)
    if package[0] == "overviews":
        handleOverviews(sock, cursor, delay, package)
    else:
        handleDetails(sock, cursor, delay, package)

    cursor.close()
    connection.close()
    print("Closed Database Connection")


# handle getOverviews:
def handleOverviews(sock, cursor, delay, args):
    print("Received command: getOverviews, and forked child process")

    consumeCpuTime(delay)

    # connect to database
    connection = connect(DATABASE_NAME)
    cursor = connection.cursor()
    print("Established Database Connection")

    # args is a list that stores all the arguments needed for sql command
    # create appropriate sql command
    sql_command, arg_arr = create_sql_command(args)
    # cursor.execute here
    cursor.execute(sql_command, arg_arr)
    # then return cursor.fetchall (all rows from database) here using dump() and flush()
    out_flow = sock.makefile(mode="wb")
    rows = cursor.fetchall()
    isSuccess = True
    dump(isSuccess, out_flow)
    dump(rows, out_flow)
    out_flow.flush()


# handle getDetails
def handleDetails(sock, cursor, delay, args):
    print("Received command: getDetails, and forked child process")

    consumeCpuTime(delay)

    # connect to database
    connection = connect(DATABASE_NAME)
    cursor = connection.cursor()
    print("Established Database Connection")

    message = ""
    isSuccess = False

    sql_command1 = "SELECT classes.courseid, classes.days, classes.starttime, classes.endtime, classes.bldg, classes.roomnum, crosslistings.dept, crosslistings.coursenum, courses.area, courses.title, courses.descrip, courses.prereqs FROM classes, crosslistings, courses WHERE classes.courseid = courses.courseid AND crosslistings.courseid = courses.courseid AND classid=? ORDER BY dept ASC, coursenum ASC"

    # fetching professors if any
    sql_command2 = "SELECT profs.profname FROM coursesprofs, profs WHERE coursesprofs.courseid=? AND coursesprofs.profid=profs.profid ORDER BY profname"

    cursor.execute(sql_command1, [args[1]])
    row = cursor.fetchone()

    # If reg.py sends a "class details" query specifying a classid that does not exist in the database, then regserver.py must write a descriptive error message to its stderr and continue executing.
    # if classid does not exist
    if row is None:
        print(f"{argv[0]}: no class with classid " +
              str(args[1]) + " exists", file=stderr)
        message = "There exists no class with the classid: " + str(args[1])
        out_flow = sock.makefile(mode="wb")
        dump(isSuccess, out_flow)
        dump(message, out_flow)
        out_flow.flush()
    else:
        firstrow = row
        courseid = str(row[0])

        message += f"Course Id: {courseid}\n\n"
        message += f"Days: {str(row[1])}\n"
        message += f"Start time: {str(row[2])}\n"
        message += f"End time: {str(row[3])}\n"
        message += f"Building: {str(row[4])}\n"
        message += f"Room: {str(row[5])}\n\n"
        message += f"Dept and Number: {str(row[6])} {str(row[7])}\n"

        row = cursor.fetchone()
        while row is not None:
            message += f"Dept and Number: {str(row[6])} {str(row[7])}\n"
            row = cursor.fetchone()

        message += '\n'
        message += f"Area: {str(firstrow[8])}\n\n"
        message += f"Title: {str(firstrow[9])}\n\n"
        message += f"Description: {str(firstrow[10])}\n\n"
        message += f"Prerequisites: {str(firstrow[11])}\n\n"

        cursor.execute(sql_command2, [courseid])
        row = cursor.fetchone()
        while row is not None:
            message += f"Professor: {str(row[0])}\n"
            row = cursor.fetchone()

        out_flow = sock.makefile(mode="wb")
        isSuccess = True
        dump(isSuccess, out_flow)
        dump(message, out_flow)
        out_flow.flush()  # if client crashes before flushing


def main(argv):
    DATABASE_NAME = "reg.sqlite"

    # argparse is user-interface related code
    # Create parser that has a description of the program and host/port positional arguments
    parser = argparse.ArgumentParser(
        description='Server for the registrar application', allow_abbrev=False)
    parser.add_argument(
        "port", type=int, help="the port at which the server should listen", nargs=1)
    parser.add_argument(
        "delay", type=int, help="the amount by which the server is delayed after a query is received", nargs=1)
    args = parser.parse_args()

    # If not running on MS Windows, then install joinChildren as
    # the handler for SIGCHLD signals.
    if name != 'nt':
        signal(SIGCHLD, joinChildren)

    try:
        # make this server bind a socket to this port and listen for a connection from a client
        port = int(argv[1])
        delay = int(argv[2])
        serverSock = socket()
        print('Opened server socket')
        serverSock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        serverSock.bind(('', port))  # can trigger unavailable port error
        print("Bound server socket to port")
        serverSock.listen()
        print('Listening')

        while True:
            try:
                sock, client_addr = serverSock.accept()
                print('Accepted connection, opened socket')

                # make sure database exists
                if not path.isfile(DATABASE_NAME):
                    print(
                        f'{argv[0]}: database reg.sqlite not found', file=stderr)
                    message = "A server error occurred. Please contact the system administrator."
                    out_flow = sock.makefile(mode="wb")
                    isSuccess = False
                    dump(isSuccess, out_flow)
                    dump(message, out_flow)
                    out_flow.flush()

                    # close socket
                    sock.close()
                    print('Closed socket')
                else:
                    # connect to database
                    # connection = connect(DATABASE_NAME)
                    # cursor = connection.cursor()
                    # print("Established Database Connection")

                    # Handle client request
                    process = Process(target=handler, args=[
                                      sock, cursor, delay])
                    process.start()

                    # close database connection
                    # cursor.close()
                    # connection.close()
                    # print("Closed Database Connection")

                    # close socket
                    sock.close()
                    print('Closed socket')

            # server error exception
            except Exception as e:
                print(f'{argv[0]}: {e}', file=stderr)
                message = "A server error occurred. Please contact the system administrator."
                out_flow = sock.makefile(mode="wb")
                isSuccess = False
                dump(isSuccess, out_flow)
                dump(message, out_flow)
                out_flow.flush()

                # close database cconnection
                cursor.close()
                connection.close()
                print("Closed Database Connection")

                # close socket
                sock.close()
                print('Closed socket')

    # triggers when we endure an unavailable port error
    except Exception as e:
        print(f'{argv[0]}: {e}', file=stderr)
        exit(1)


if __name__ == '__main__':
    main(argv)
