# COS 333 Assignment 4: A Registrar Application Using Graphical User Interface and Network Programming
# Authors: Sam Liang, Sumanth Maddirala
# Description: Presents information on Princeton Course Offerings based on specified criteria

from os import path
from sys import argv, stderr, exit
from socket import socket, SOL_SOCKET, SO_REUSEADDR
from pickle import dump, load
from threading import Thread
from queue import Queue
from sqlite3 import connect
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QFrame
from PyQt5.QtWidgets import QLabel, QGridLayout, QPushButton, QVBoxLayout, QFormLayout, QHBoxLayout
from PyQt5.QtWidgets import QLineEdit, QTextEdit, QScrollArea
from PyQt5.QtWidgets import QSlider, QCheckBox, QRadioButton
from PyQt5.QtWidgets import QListWidget, QDesktopWidget, QMessageBox
from PyQt5.QtGui import QFont, QEnterEvent
from PyQt5.QtCore import Qt, QItemSelectionModel, QTimer
import argparse
import textwrap
from database_handler import create_sql_command

textThread = None


# Gets all classes in the listbox
class TextThread (Thread):

    def __init__(self, host, port, packet, queue):
        Thread.__init__(self)
        self._host = host
        self._port = port
        self._packet = packet
        self._queue = queue
        self._shouldStop = False

    def stop(self):
        self._shouldStop = True

    def run(self):
        # send the values to regserver.py
        # keep everything in a try loop in case multiple signals come in so doesn't terminate
        try:
            sock = socket()
            sock.connect((self._host, self._port))
            out_flow = sock.makefile(mode='wb')
            dump(self._packet, out_flow)
            out_flow.flush()

            # retrieve the values from regserver.py
            in_flow = sock.makefile(mode='rb')
            isSuccess = load(in_flow)
            db_rows = load(in_flow)

            # close connection
            sock.close()

            if self._shouldStop:
                return
            self._queue.put((isSuccess, db_rows))
        except Exception as e:
            # print(f'{argv[0]}: {e}', file=stderr)
            self._queue.put((False, "[Errno 111] Connection refused"))


def main(argv):
    # argparse is user-interface related code
    # Create parser that has a description of the program and host/port positional arguments
    parser = argparse.ArgumentParser(
        description='Client for the registrar application', allow_abbrev=False)
    parser.add_argument(
        "host", type=str, help="the host on which the server is running", nargs=1)
    parser.add_argument(
        "port", type=int, help="the port at which the server is listening", nargs=1)
    args = parser.parse_args()

    # get the host and port
    host = argv[1]
    port = int(argv[2])

    queue = Queue()

    # initiation code line
    app = QApplication(argv)

    # Labels and LineEdits for a dept, coursenum, area, title
    deptLab = QLabel("Dept: ")
    deptLab.setAlignment(Qt.AlignRight)
    deptLine = QLineEdit()

    courseLab = QLabel("Number: ")
    courseLab.setAlignment(Qt.AlignRight)
    courseNumLine = QLineEdit()

    areaLab = QLabel("Area: ")
    areaLab.setAlignment(Qt.AlignRight)
    areaLine = QLineEdit()

    titleLab = QLabel("Title: ")
    titleLab.setAlignment(Qt.AlignRight)
    titleLine = QLineEdit()

    # list box that can scroll vertically and horizontally
    list_box = QListWidget()
    list_box.setFont(QFont("Courier", 10))

    # submit button
    # submit_but = QPushButton("Submit")

    top_layout = QGridLayout()
    top_layout.setSpacing(0)
    top_layout.setContentsMargins(0, 0, 0, 0)
    top_layout.setRowStretch(0, 0)
    top_layout.setRowStretch(1, 0)
    top_layout.setRowStretch(2, 0)
    top_layout.setRowStretch(3, 0)
    top_layout.setColumnStretch(0, 0)
    top_layout.setColumnStretch(1, 1)
    top_layout.setColumnStretch(2, 0)

    # labels
    top_layout.addWidget(deptLab, 0, 0)
    top_layout.addWidget(courseLab, 1, 0)
    top_layout.addWidget(areaLab, 2, 0)
    top_layout.addWidget(titleLab, 3, 0)

    # line edits
    top_layout.addWidget(deptLine, 0, 1)
    top_layout.addWidget(courseNumLine, 1, 1)
    top_layout.addWidget(areaLine, 2, 1)
    top_layout.addWidget(titleLine, 3, 1)

    # submit button
    # top_layout_right = QVBoxLayout()
    # top_layout_right.setSpacing(0)
    # top_layout_right.setContentsMargins(0, 0, 0, 0)
    # top_layout_right.addWidget(submit_but)
    # top_layout_right.setAlignment(Qt.AlignCenter)
    # top_layout.addLayout(top_layout_right, 0, 2, 4, 1)

    # top layout frame
    top_frame = QFrame()
    top_frame.setLayout(top_layout)

    # bottom list layout frame
    bot_layout = QGridLayout()
    bot_layout.setSpacing(0)
    bot_layout.setContentsMargins(0, 0, 0, 0)
    bot_layout.addWidget(list_box, 0, 0)
    bot_frame = QFrame()
    bot_frame.setLayout(bot_layout)

    # overarching frame layout and frame
    centralFrameLayout = QGridLayout()
    centralFrameLayout.setSpacing(0)
    centralFrameLayout.setContentsMargins(0, 0, 0, 0)
    centralFrameLayout.setRowStretch(0, 0)
    centralFrameLayout.setRowStretch(1, 1)
    centralFrameLayout.setColumnStretch(0, 1)
    centralFrameLayout.addWidget(top_frame, 0, 0)
    centralFrameLayout.addWidget(bot_frame, 1, 0)
    centralFrame = QFrame()
    centralFrame.setLayout(centralFrameLayout)

    window = QMainWindow()
    window.setWindowTitle('Princeton University Class Search')
    window.setCentralWidget(centralFrame)
    screenSize = QDesktopWidget().screenGeometry()
    window.resize(screenSize.width()//2, screenSize.height()//2)

    # extracts the input in each of the 4 lines as the text is written, create a socket connection with regserver.py, and send the input to regserver.py. Retrieve the return value from regserver.py and close socket connection
    def retrieveText():
        print("Sent command: getOverviews")
        global textThread
        dept = str(deptLine.text())
        course_num = str(courseNumLine.text())
        area = str(areaLine.text())
        title = str(titleLine.text())

        # prepare the packet to send to regserver.py
        packet = ["overviews", dept, course_num, area, title]
        if textThread is not None:
            textThread.stop()
        textThread = TextThread(host, port, packet, queue)
        textThread.start()

    def retrieveDetails():
        print("Sent command: getDetail")
        # get the courseId from the selection
        selected_str = str(list_box.currentItem().text())
        # selection = selectedRow[0]
        # print(selection)
        words = selected_str.split()
        class_id = int(words[0])
        packet = ["details", class_id]

        # send the values to regserver.py
        try:
            sock = socket()
            sock.connect((host, port))
            out_flow = sock.makefile(mode='wb')
            dump(packet, out_flow)
            out_flow.flush()

            # retrieve the values from regserver.py
            in_flow = sock.makefile(mode='rb')
            isSuccess = load(in_flow)
            message = load(in_flow)

            # close connection
            sock.close()

        except:
            isSuccess = False
            message = "[Errno 111] Connection refused"

        if not isSuccess:
            # display error with classid not existing in database
            msgBox = QMessageBox.critical(
                window, 'Server Error', message)
        else:
            # create and display information via messageBox
            msgBox = QMessageBox.information(
                window, 'Class Details', message)

    # our queue contains a boolean, indicating if there is an error raised or not for a key
    # and the rows of the class details message box as the value
    def pollQueue():
        while not queue.empty():
            isSuccess, db_rows = queue.get()

            if not isSuccess:
                msgBox = QMessageBox.critical(window, 'Server Error', db_rows)

            else:
                # clear list box and put appropriate items
                list_box.clear()
                for row in db_rows:
                    line_string = "{:>5}{:>4}{:>5}{:>4} {}".format(
                        str(row[0]).strip(), str(row[1]).strip(), str(row[2]).strip(), str(row[3]).strip(), str(row[4]).strip())
                    list_box.addItem(line_string)

                # automatically highlight first row each time
                list_box.setCurrentRow(0)

    timer = QTimer()
    timer.timeout.connect(pollQueue)
    timer.setInterval(100)  # milliseconds
    timer.start()

    window.show()

    while True:
        # retrieve values when enter is clicked in one of the line edits (unnecessary w/ text changed)
        # deptLine.returnPressed.connect(retrieveText)
        # courseNumLine.returnPressed.connect(retrieveText)
        # areaLine.returnPressed.connect(retrieveText)
        # titleLine.returnPressed.connect(retrieveText)

        # retrieve values when submit button is clicked
        # submit_but.clicked.connect(retrieveText)
        deptLine.textChanged.connect(retrieveText)
        courseNumLine.textChanged.connect(retrieveText)
        areaLine.textChanged.connect(retrieveText)
        titleLine.textChanged.connect(retrieveText)

        # open details when user double clicks or hits enter on a list widget item
        list_box.itemActivated.connect(retrieveDetails)

        retrieveText()
        # global textThread  # perhaps this should be deleted?
        # if textThread is not None:
        #     textThread.stop()
        # packet = ["overviews", "", "", "", ""]
        # textThread = TextThread(host, port, packet, queue)
        # textThread.start()

        timer = QTimer()
        timer.timeout.connect(pollQueue)
        timer.setInterval(100)  # milliseconds
        timer.start()

        window.show()
        exit(app.exec_())


if __name__ == '__main__':
    main(argv)
