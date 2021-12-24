#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import argparse
import pymysql
import time

# If Python is version 2.7, encoding problems can reload sys configuration
try:
    import sys
    import os

    reload(sys)
    sys.setdefaultencoding('utf-8')
except:
    pass


def main():
    '''
    When no library name or table name is entered, Analyze operation is not performed.
    When you enter a library name without entering a table name, all tables in the library are analyzed.
    When no library name is entered, but a table name is entered, the entered table is analyzed.
    No other cases will be analyzed.
    '''
    args = parse_args()
    table, db = args.tables, args.database
    healthy = args.stats_healthy
    if table is None and db is None:
        print("Please enter the relevant information for the analyze table.")
    elif table is None and db is not None:
        for _db in db.split(","):
            analyze_db(_db, healthy)
            print(
                "Statistics for all tables in Analyze {} library succeeded~\n".format(_db))
    elif table is not None and db is None:
        for db_table in table.split(","):
            _db, _table = db_table.split(".")[0], db_table.split(".")[1]
            analyze_table(_db, _table, healthy)
            print("Success Analyze all tables")
    else:
        print("Please enter the table that requires analyze in the correct format")


def parser_stats(db_name, table_name):
    # concat sql
    _sql = "show stats_healthy where Db_name in ('{}') and Table_name in ('{}');".format(
        db_name, table_name)
    result = mysql_execute(_sql)[0]["Healthy"]

    return result


def analyze_table(db_name, table_name, healthy):
    # time format
    time_format = time.strftime("%Y-%m-%d %H:%M:%S",
                                time.localtime())
    # Analyze the table
    _health = parser_stats(db_name, table_name)
    if _health <= int(healthy):
        mysql_execute("use {}".format(db_name),
                      "analyze table {}".format(table_name))
        print("{} Analyze table {}.{} Sucessful".format(
            time_format, db_name, table_name))
    else:
        print("{} db: {}, table: {} health: {},skip analyze".format(time_format,
                                                                    db_name, table_name, _health))


def analyze_db(db_name, healthy):
    # Analyze all tables in the database
    table_names = mysql_execute("use {}".format(db_name), "show tables;")
    for table_name in table_names:
        table_name = table_name["Tables_in_{}".format(db_name)]
        _health = parser_stats(db_name, table_name)
        if _health <= int(healthy):
            analyze_table(db_name, table_name, healthy)
        else:
            print("db: {}, table: {} health: {},skip analyze".format(
                db_name, table_name, _health))


def mysql_execute(*_sql):
    # Connect to MySQL and execute SQL commands
    # content = ""
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

    # with connection.cursor() as cursor:
    cursor = connection.cursor()
    for sql in _sql:
        cursor.execute(sql)
    content = cursor.fetchall()
    connection.commit()
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
    parser.add_argument(
        "-d",
        dest="database",
        help="Database name, for example: test,test1, default: None",
        default=None)
    parser.add_argument(
        "-t",
        dest="tables",
        help="Table name (database.table), for example: test.test,test.test2, default: None",
        default=None)
    parser.add_argument("-sh", dest="stats_healthy",
                        help="Table stats healthy, If it is below the threshold, then analyze~", default=100)

    args = parser.parse_args()

    return args


if __name__ == "__main__":
    main()
