#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import argparse
import pymysql
import csv
import time

## If Python is version 2.7, encoding problems can reload sys configuration
# import sys

# reload(sys)
# sys.setdefaultencoding('utf-8')


def main():
    args = parse_args()
    if args.column is 'all':
        fieldnames = mysql_execute(None, None, "use {};".format(args.database),
                                   "desc {};".format(args.table))
        fieldnames = [i['Field'] for i in fieldnames]
        mysql_execute('csv', fieldnames, "use {};".format(args.database),
                      "select * from {};".format(args.table))
    else:
        fieldnames = str(args.column).split(',')
        mysql_execute(
            'csv', fieldnames, "use {};".format(args.database),
            "select {} from {};".format(str(args.column), args.table))


def mysql_execute(file_name=None, fieldnames=[], *_sql):
    args = parse_args()
    host = args.mysql.split(':', 1)[0]
    port = int(args.mysql.split(':', 1)[1])
    try:
        connection = pymysql.connect(host=host,
                                     user=args.user,
                                     password=args.password,
                                     port=port,
                                     charset='utf8mb4',
                                     cursorclass=pymysql.cursors.DictCursor)
    except all as error:
        print("Connect Database is failed~\n", error)

    try:
        with connection.cursor() as cursor:
            cursor.execute("SET NAMES utf8mb4")
            for sql in _sql:
                cursor.execute(sql)

            if file_name is not 'csv':
                content = cursor.fetchall()
            else:
                file_name = "{}.{}.csv".format(args.database, args.table)
                start_time = time.time()
                with open(file_name, 'a+', newline='') as csvfile:
                    writer = csv.DictWriter(csvfile,
                                            fieldnames=fieldnames,
                                            quoting=csv.QUOTE_NONNUMERIC)
                    writer.writeheader()
                    for content in cursor:
                        writer.writerow(content)
                end_time = time.time()
                print("Write {} is Successful, Cost time is {}".format(
                    file_name, end_time - start_time))

            connection.commit()
    except all as error:
        print(
            "SQL {} execution failed~ \n Please check table or database exists or not!,error: {}".format(
                _sql), error)

    finally:
        cursor.close()
        connection.close()

    return content


def parse_args():
    parser = argparse.ArgumentParser(description="Export data to CSV")
    parser.add_argument("-tp",
                        dest="mysql",
                        help="TiDB Port, default: 127.0.0.1:4000",
                        default="127.0.0.1:4000")
    parser.add_argument("-u",
                        dest="user",
                        help="TiDB User, default: root",
                        default="root")
    parser.add_argument("-p",
                        dest="password",
                        help="TiDB Password, default: null",
                        default="")
    parser.add_argument("-d",
                        dest="database",
                        help="database name, default: test",
                        default="test")
    parser.add_argument("-t",
                        dest="table",
                        help="Table name, default: test",
                        default="test")
    parser.add_argument(
        "-c",
        dest="column",
        help="Table Column, for example: id,name, default: all",
        default="all")

    args = parser.parse_args()

    return args


if __name__ == "__main__":
    main()
