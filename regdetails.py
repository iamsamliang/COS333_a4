# COS 333 Assignment 1: A Registrar Application Using Database Programming
# Authors: Sam Liang, Sumanth Maddirala
# Description: Presents detailed information on Princeton Course Offerings based on a course's class_id

from os import path
from sys import argv, stderr, exit
from sqlite3 import connect
import argparse
import textwrap

# rewrite as a helper function named course_details


def main(argv):
    DATABASE_NAME = "reg.sqlite"

    # user-interface code
    if not path.isfile(DATABASE_NAME):
        print(f'{argv[0]}: database reg.sqlite not found', file=stderr)
        exit(1)

    # user-interface code
    # Create parser that has a description of the program. Also, add optional
    # arguments for the client to call and pass in values
    parser = argparse.ArgumentParser(
        description='Registrar application: show details about a class', allow_abbrev=False)
    parser.add_argument(
        "classid", type=int, help="the id of the class whose details should be shown", nargs=1)
    args = parser.parse_args()

    # database code
    try:
        connection = connect(DATABASE_NAME)
        cursor = connection.cursor()

        sql_command1 = "SELECT classes.courseid, classes.days, classes.starttime, classes.endtime, classes.bldg, classes.roomnum, crosslistings.dept, crosslistings.coursenum, courses.area, courses.title, courses.descrip, courses.prereqs FROM classes, crosslistings, courses WHERE classes.courseid = courses.courseid AND crosslistings.courseid = courses.courseid AND classid=? ORDER BY dept ASC, coursenum ASC"

        # fetching professors if any
        sql_command2 = "SELECT profs.profname FROM coursesprofs, profs WHERE coursesprofs.courseid=? AND coursesprofs.profid=profs.profid ORDER BY profname"

        cursor.execute(sql_command1, args.classid)
        row = cursor.fetchone()

        if row is None:
            print(f"{argv[0]}: no class with classid " +
                  str(args.classid[0]) + " exists", file=stderr)
            exit(1)

        firstrow = row
        courseid = str(row[0])
        wrapper = textwrap.TextWrapper(
            width=72, break_long_words=False)
        wrapper_spec = textwrap.TextWrapper(
            width=72)
        print(wrapper.fill(f"Course Id: {courseid}"))
        print()
        print(f"Days: {str(row[1])}")
        print(f"Start time: {str(row[2])}")
        print(f"End time: {str(row[3])}")
        print(f"Building: {str(row[4])}")
        print(f"Room: {str(row[5])}")
        print()
        print(
            wrapper.fill(f"Dept and Number: {str(row[6])} {str(row[7])}"))

        row = cursor.fetchone()
        while row is not None:
            print(
                wrapper.fill(f"Dept and Number: {str(row[6])} {str(row[7])}"))
            row = cursor.fetchone()

        print()
        # print(wrapper.fill("Area: " + str(firstrow[8])))
        print(f"Area: {str(firstrow[8])}")
        print()
        print(wrapper.fill(f"Title: {str(firstrow[9])}"))
        print()
        print(wrapper.fill(f"Description: {str(firstrow[10])}"))
        print()
        print(wrapper_spec.fill(f"Prerequisites: {str(firstrow[11])}"))
        print()

        cursor.execute(sql_command2, [courseid])
        row = cursor.fetchone()
        while row is not None:
            print(f"Professor: {str(row[0])}")
            row = cursor.fetchone()

        cursor.close()
        connection.close()

# exit(2) case handled by arg_parse module, exit(1) case handled on lines 11-18
# If some other program has corrupted the reg.sqlite database file
# (missing table, missing field, etc.) such that a database query
# performed by reg.py throws an exception, then reg.py must write
# the message that is within that exception to stderr. exit status 1
    except Exception as e:
        print(f'{argv[0]}: {e}', file=stderr)
        exit(1)


if __name__ == '__main__':
    main(argv)