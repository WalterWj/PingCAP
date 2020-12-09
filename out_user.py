#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import argparse
import pymysql
import os

## If Python is version 2.7, encoding problems can reload sys configuration
try:
    import sys

    reload(sys)
    sys.setdefaultencoding('utf-8')
except:
    pass


def main():
    args = parse_args()
    _set_pwd = "select user,host,authentication_string from mysql.user;"
    context = mysql_execute(_set_pwd)
    for i in context:
        write_file(i['user'], i['host'], i['authentication_string'])
        print("User: '{}'@'{}' is OK".format(i['user'], i['host']))


def write_file(user_name, hosts, authentication_string):
    # update and grants
    _show_grants = "SHOW GRANTS FOR '{}'@'{}'".format(user_name, hosts)
    grant_context = mysql_execute(_show_grants)
    _set_pwd = "update mysql.user set `authentication_string`='{}' where user='{}' and host='{}';".format(
        authentication_string, user_name, hosts)
    _create_user = "create user '{}'@'{}';".format(user_name, hosts)
    with open('tidb_users.sql', 'a+') as f:
        f.write("-- '{}'@'{}' \n".format(user_name, hosts))
        f.write("{} \n".format(_create_user))
        f.write("{} \n".format(_set_pwd))
        for i in grant_context:
            i = list(i.values())
            f.write("{};\n".format(i[0]))
        f.write("\n")


def mysql_execute(*_sql):
    # Connect to MySQL and execute SQL commands
    args = parse_args()
    config = {
        "host": args.mysql,
        "port": int(args.port),
        "user": args.user,
        "password": args.password,
        "charset": 'utf8mb4',
        "cursorclass": pymysql.cursors.DictCursor
    }

    connection = pymysql.connect(**config)
    cursor = connection.cursor()
    try:
        for sql in _sql:
            cursor.execute(sql)
            content = cursor.fetchall()
            connection.commit()
    except:
        print(
            "SQL {} execution failed~ \nPlease check table or database exists or not!"
            .format(_sql))
    finally:
        cursor.close()
        connection.close()

    return content


def parse_args():
    # Incoming parameters
    parser = argparse.ArgumentParser(
        description="Update table statistics manually")
    parser.add_argument("-P",
                        dest="port",
                        help="tidb port, default: 4000",
                        default=4000)
    parser.add_argument("-H",
                        dest="mysql",
                        help="Database address, default: 127.0.0.1",
                        default="127.0.0.1")
    parser.add_argument("-u",
                        dest="user",
                        help="Database account, default: root",
                        default="root")
    parser.add_argument("-p",
                        dest="password",
                        help="Database password, default: null",
                        default="")

    args = parser.parse_args()

    return args


if __name__ == "__main__":
    main()
