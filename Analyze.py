#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import json
import argparse
import pymysql
import subprocess
import os
import time
import tarfile
import shutil

## If Python is version 2.7, encoding problems can reload sys configuration
try:
    import sys

    reload(sys)
    sys.setdefaultencoding('utf-8')
except:
    pass

def main():
    args = parse_args()
    table, db = args.tables, args.database
    if table is None and db is None:
        print("Please enter the relevant information for the analyze table.")
    elif table is None and db is not None:
        for _db in db.split(","):
            analyze_db(_db)
            print("Statistics for all tables in Analyze {} library succeeded~\n".format(_db))
    elif table is not None and  db is "test":
        for db_table in table.split(","):
            _db, _table = db_table.split(".")[0], db_table.split(".")[1]
            analyze_table(_db, _table)
            print("Success Analyze all tables")
    else:
        print("Please enter the table that requires analyze in the correct format")


def analyze_table(db_name, table_name):
    # Analyze the table
    mysql_execute("use {}".format(db_name), "analyze table {}".format(table_name))
    print("Analyze table {}.{} Sucessful".format(db_name, table_name))

def analyze_db(db_name):
    # Analyze all tables in the database
    table_names = mysql_execute("use {}".format(db_name), "show tables;")
    for table_name in table_names:
        table_name = table_name["Tables_in_{}".format(db_name)]
        analyze_table(db_name, table_name)

def mysql_execute(*_sql):
    # Connect to MySQL and execute SQL commands
    args = parse_args()
    config = {
        "host": args.mysql,
        "port": args.port,
        "user": args.user,
        "password": args.password,
        "charset": 'utf8mb4',
        "cursorclass": pymysql.cursors.DictCursor
    }

    try:
        connection = pymysql.connect(**config)
    except:
        print("Connect Database is failed~")

    try:
        with connection.cursor() as cursor:
            for sql in _sql:
                cursor.execute(sql)
            content = cursor.fetchall()
            connection.commit()
    except:
        print(
            "SQL {} execution failed~ \nPlease check table or database exists or not!".format(
                _sql))
    finally:
        cursor.close()
        connection.close()

    return content

def parse_args():
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
                        default="123")
    parser.add_argument(
        "-d",
        dest="database",
        help="Database name, for example: test,test1, default: test",
        default="test")
    parser.add_argument(
        "-t",
        dest="tables",
        help=
        "Table name (database.table), for example: test.test,test.test2, default: None",
        default=None)

    args = parser.parse_args()

    return args

if __name__ == "__main__":
    main()
