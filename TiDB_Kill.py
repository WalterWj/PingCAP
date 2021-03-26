#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import argparse
import pymysql

# If Python is version 2.7, encoding problems can reload sys configuration
try:
    import sys

    reload(sys)
    sys.setdefaultencoding('utf-8')
except:
    pass


def main():
    args = parse_args()
    _set_pwd = ""


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
        description="Kill TiDB session by id")
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
    parser.add_argument("-a",
                        dest="advertiseAddress",
                        help="TiDB Address, default: null",
                        default="")
    parser.add_argument("-ap",
                        dest="advertisePort",
                        help="TiDB Port, default: 4000",
                        default="4000")
    parser.add_argument("-id",
                        dest="sessionId",
                        help="session id, default: null",
                        default="")
    args = parser.parse_args()

    return args


if __name__ == "__main__":
    main()
