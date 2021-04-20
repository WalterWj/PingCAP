#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import argparse
import pymysql


def main():
    args = parse_args()
    dbname = args.database
    u_dbname, t_sql = "use {}".format(dbname), "show tables;"
    t_table = mysql_execute(u_dbname, t_sql)
    for tb in t_table:
        tb_name = tb["Tables_in_{}".format(dbname)]
        fchecksum = check_table(dbname, tb_name, "f")
        tchecksum = check_table(dbname, tb_name, "t")
        if fchecksum == tchecksum:
            print(
                "Checksum is sucessfull, DB name is:{},Table name is:{}, Checksum is {}"
                .format(dbname, tb_name, fchecksum))
        else:
            print(
                "Checksum is failed,DB name is:{},Table name is:{}, f-Checksum is {}, t-Checksum is {}"
                .format(dbname, tb_name, fchecksum, tchecksum))


def check_table(db_name, table_name, mode):
    check_sql = "admin checksum table `{}`".format(table_name)
    set_scan = "set tidb_checksum_table_concurrency = 200"
    if mode == "f":
        checksum = mysql_execute("use {}".format(db_name), set_scan, check_sql)
    else:
        checksum = mysql_execute1("use {}".format(db_name), set_scan,
                                  check_sql)

    checksum = checksum[0]["Total_bytes"]

    return checksum


def mysql_execute1(*_sql):
    # connect mysql
    args = parse_args()
    host = args.tmysql.split(':', 1)[0]
    port = int(args.tmysql.split(':', 1)[1])

    config = {
        "host": host,
        "user": args.tuser,
        "password": args.tpassword,
        "port": port,
        "charset": 'utf8mb4',
        "cursorclass": pymysql.cursors.DictCursor
    }

    connection = pymysql.connect(**config)
    cursor = connection.cursor()
    for sql in _sql:
        cursor.execute(sql)
        content = cursor.fetchall()
        connection.commit()

    return content


def mysql_execute(*_sql):
    # connect mysql
    args = parse_args()
    host = args.fmysql.split(':', 1)[0]
    port = int(args.fmysql.split(':', 1)[1])

    config = {
        "host": host,
        "user": args.fuser,
        "password": args.fpassword,
        "port": port,
        "charset": 'utf8mb4',
        "cursorclass": pymysql.cursors.DictCursor
    }

    connection = pymysql.connect(**config)
    cursor = connection.cursor()
    for sql in _sql:
        cursor.execute(sql)
        content = cursor.fetchall()
        connection.commit()

    return content


def parse_args():
    parser = argparse.ArgumentParser(description="Check tables")
    parser.add_argument(
        "-hf",
        dest="fmysql",
        help="Database address and port, default: 127.0.0.1:4000",
        default="127.0.0.1:4000")
    parser.add_argument("-uf",
                        dest="fuser",
                        help="Database account, default: root",
                        default="root")
    parser.add_argument("-pf",
                        dest="fpassword",
                        help="Database password, default: null",
                        default="")
    parser.add_argument(
        "-ht",
        dest="tmysql",
        help="Database address and port, default: 127.0.0.1:4000",
        default="127.0.0.1:4000")
    parser.add_argument("-ut",
                        dest="tuser",
                        help="Database account, default: root",
                        default="root")
    parser.add_argument("-pt",
                        dest="tpassword",
                        help="Database password, default: null",
                        default="")
    parser.add_argument(
        "-d",
        dest="database",
        help="Database name, for example: test, default: None",
        default=None)
    args = parser.parse_args()

    return args


if __name__ == "__main__":
    main()
