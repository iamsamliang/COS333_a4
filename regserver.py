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
from database import Database
# from database_handler import create_sql_command

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
def handler(sock, delay):
    in_flow = sock.makefile(mode="rb")
    package = load(in_flow)
    # Grab the determiner
    method = package[0]
    # Change package to only have the arguments
    args = package[1:]
    if method == "overviews":
        handleOverviews(sock, delay, args)
    else:
        # args[0] = classid
        handleDetails(sock, delay, args[0])

    # cursor.close()
    # connection.close()
    # print("Closed Database Connection")


# handle getOverviews:
def handleOverviews(sock, delay, form_args):
    print("Forked child process")
    print("Received command: getOverviews")

    try:
        consumeCpuTime(delay)

        # connect to database
        database = Database()
        database.connect()
        rows = database.search(form_args)
        database.disconnect()

        # Old code
        # args is a list that stores all the arguments needed for sql command
        # create appropriate sql command
        # sql_command, arg_arr = create_sql_command(args)
        # cursor.execute here
        # cursor.execute(sql_command, arg_arr)
        # Old code

        # then return cursor.fetchall (all rows from database) here using dump() and flush()
        out_flow = sock.makefile(mode="wb")
        # rows = cursor.fetchall() ---- Old code
        isSuccess = True
        dump(isSuccess, out_flow)
        dump(rows, out_flow)
        out_flow.flush()

        sock.close()
        print('Closed socket in child process')
        print('Exiting child process')
    except Exception as e:
        print(f'{argv[0]}: {e}', file=stderr)
        message = "A server error occurred. Please contact the system administrator."
        out_flow = sock.makefile(mode="wb")
        isSuccess = False
        dump(isSuccess, out_flow)
        dump(message, out_flow)
        out_flow.flush()

        # close database cconnection
        # database.disconnect()
        # print("Closed Database Connection")

        # close socket
        sock.close()
        print('Closed socket in child process')
        print('Exiting child process')


# handle getDetails
def handleDetails(sock, delay, class_id):
    try:
        print("Forked child process")
        print("Received command: getDetails")

        consumeCpuTime(delay)

        # connect to database
        database = Database()
        database.connect()
        isSuccess, message = database.class_details(class_id)
        database.disconnect()

        out_flow = sock.makefile(mode="wb")
        dump(isSuccess, out_flow)
        dump(message, out_flow)
        out_flow.flush()

        sock.close()
        print('Closed socket in child process')
        print('Exiting child process')
    except Exception as e:
        print(f'{argv[0]}: {e}', file=stderr)
        message = "A server error occurred. Please contact the system administrator."
        out_flow = sock.makefile(mode="wb")
        isSuccess = False
        dump(isSuccess, out_flow)
        dump(message, out_flow)
        out_flow.flush()

        # close database cconnection
        # database.disconnect()
        # print("Closed Database Connection")

        # close socket
        sock.close()
        print('Closed socket in child process')
        print('Exiting child process')


def main(argv):
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
        print('OS:', name)
        print('CPU count:', cpu_count())
        print('Opened server socket')
        serverSock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        serverSock.bind(('', port))  # can trigger unavailable port error
        print("Bound server socket to port")
        serverSock.listen()
        print('Listening')

        while True:
            sock, client_addr = serverSock.accept()
            print('Accepted connection, opened socket')

            # Handle client request
            process = Process(target=handler, args=[sock, delay])
            process.start()

            # close socket
            sock.close()
            print('Closed socket in parent process')

    # triggers when we endure an unavailable port error
    except Exception as e:
        print(f'{argv[0]}: {e}', file=stderr)
        exit(1)


if __name__ == '__main__':
    main(argv)
