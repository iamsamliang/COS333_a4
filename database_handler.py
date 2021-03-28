# takes in an argument string and places # before all SQL special symbols (_, %) so that SQL interprets them not as special symbols but as regular characters. Returns the modified strings
def special_char_mod(input_str: str) -> str:
    i = 0
    char_arr = list(input_str)
    while i in range(len(char_arr)):
        if char_arr[i] in ["%", "_"]:
            char_arr.insert(i, "#")
            i += 1
        i += 1
    return ''.join(char_arr)


# generates a sql command that selects course information for courses matching a specified course criterion. also returns a tuple of arguments containing the expressions for the placeholder ? symbols in the sql_command
def create_sql_command(args):
    sql_command = "SELECT classes.classid, crosslistings.dept, crosslistings.coursenum, courses.area, courses.title FROM classes, crosslistings, courses WHERE classes.courseid = courses.courseid AND crosslistings.courseid = courses.courseid"

    arg_arr = []

    if args[1]:
        sql_command += " AND dept LIKE ? ESCAPE '#'"
        result = special_char_mod(args[1])
        arg_arr.append("%" + result + "%")

    if args[2]:
        sql_command += " AND coursenum LIKE ? ESCAPE '#'"
        result = special_char_mod(args[2])
        arg_arr.append("%" + result + "%")

    if args[3]:
        sql_command += " AND area LIKE ? ESCAPE '#'"
        result = special_char_mod(args[3])
        arg_arr.append("%" + result + "%")

    if args[4]:
        sql_command += " AND title LIKE ? ESCAPE '#'"
        result = special_char_mod(args[4])
        arg_arr.append("%" + result + "%")

    sql_command += " ORDER BY dept ASC, coursenum ASC, classid ASC"

    return sql_command, arg_arr