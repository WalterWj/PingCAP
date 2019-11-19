#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import argparse
import pymysql
import csv

## If Python is version 2.7, encoding problems can reload sys configuration
# import sys

# reload(sys)
# sys.setdefaultencoding('utf-8')

def main():
    args = parse_args()
    if args.column is 'all':
        all_content = mysql_execute("use {};".format(args.database), "select * from {};".format(args.table))
        try:
            file_name = "{}.{}.csv".format(args.database, args.table)
            with open(file_name, 'a+',newline='') as csvfile:
                fieldnames = ['id', 'name']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames, quoting=csv.QUOTE_NONNUMERIC)

                writer.writeheader()
                for content in all_content:
                    writer.writerow(content)
                print("Write {} is Successful".format(file_name))

        except all as error:
            print("Write {} error!,and {}".format(file_name, error))


def mysql_execute(*_sql):
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
        print("Connect Database is failed~\n",error)

    try:
        with connection.cursor() as cursor:
            cursor.execute("SET NAMES utf8mb4")
            for sql in _sql:
                cursor.execute(sql)
            content = cursor.fetchall()
            connection.commit()
    except:
        print(
            "SQL {} execution failed~ \n Please check table or database exists or not!".format(
                _sql))

    finally:
        cursor.close()
        connection.close()

    return content


def parse_args():
    parser = argparse.ArgumentParser(
        description="Export data to CSV")
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
    parser.add_argument("-c",
                        dest="column",
                        help="Table Column, default: all",
                        default="all")                       
    # parser.add_argument("table", help="Table name")
    args = parser.parse_args()
    return args


if __name__ == "__main__":
    main()
