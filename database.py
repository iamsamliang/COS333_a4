from sqlite3 import connect
from sys import argv, stderr
from os import path
import database_handler


class Database():

    def __init__(self):
        self._connection = None

    def connect(self):
        DATABASE_NAME = 'reg.sqlite'
        if not path.isfile(DATABASE_NAME):
            print(f"{argv[0]}: database reg.sqlite not found", file=stderr)
            raise Exception(e)
                # 'A server error occurred. Please contact the system administrator.')
        self._connection = connect(DATABASE_NAME)

    def disconnect(self):
        self._connection.close()

    def search(self, form_args):
        try:
            cursor = self._connection.cursor()

            # form_args is a list that stores all the arguments needed for sql command
            # create appropriate sql command
            sql_command, arg_arr = database_handler.create_sql_command(
                form_args)
            # cursor.execute here
            cursor.execute(sql_command, arg_arr)

            rows = []
            row = cursor.fetchone()
            while row is not None:
                rows.append(row)
                row = cursor.fetchone()
            cursor.close()
            return rows
        except Exception as e:
            cursor.close()
            self.disconnect()
            raise Exception(
                'A server error occurred. Please contact the system administrator.')

    def class_details(self, class_id):
        try:
            cursor = self._connection.cursor()

            isSuccess = False
            message = ""

            sql_command1 = "SELECT classes.courseid, classes.days, classes.starttime, classes.endtime, classes.bldg, classes.roomnum, crosslistings.dept, crosslistings.coursenum, courses.area, courses.title, courses.descrip, courses.prereqs FROM classes, crosslistings, courses WHERE classes.courseid = courses.courseid AND crosslistings.courseid = courses.courseid AND classid=? ORDER BY dept ASC, coursenum ASC"

            # fetching professors if any
            sql_command2 = "SELECT profs.profname FROM coursesprofs, profs WHERE coursesprofs.courseid=? AND coursesprofs.profid=profs.profid ORDER BY profname"

            cursor.execute(sql_command1, [class_id])
            row = cursor.fetchone()

            # If reg.py sends a "class details" query specifying a classid that does not exist in the database, then regserver.py must write a descriptive error message to its stderr and continue executing.
            # if classid does not exist
            if row is None:
                print(f"{argv[0]}: no class with classid " +
                      str(class_id) + " exists", file=stderr)
                message = "There exists no class with the classid: " + \
                    str(class_id)
                isSuccess = False
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
                isSuccess = True

            cursor.close()
            return isSuccess, message
        except Exception as e:
            cursor.close()
            self.disconnect()
            raise Exception(
                'A server error occurred. Please contact the system administrator.')
