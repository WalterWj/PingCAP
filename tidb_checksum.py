#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import argparse
import pymysql
import time
import json


def main():
    args = parse_args()
    dbname = args.database
    u_dbname, t_sql = "use {}".format(dbname), "show tables;"
    t_table = mysql_execute(u_dbname, t_sql)
    tso = mysql_execute1("select checkPoint from tidb_binlog.checkpoint")
    tso = json.loads(tso[0]["checkPoint"])
    ftso = tso["ts-map"]["primary-ts"]
    ttso = tso["ts-map"]["secondary-ts"]
    for tb in t_table:
        tb_name = tb["Tables_in_{}".format(dbname)]
        fkvs, fbytes = check_table(dbname, tb_name, ftso, "f")
        tkvs, tbytes = check_table(dbname, tb_name, ttso,"t")
        if fbytes == tbytes and fkvs == tkvs:
            print(
                "Check successful, DB name is:{},Table name is:{}, bytes is {}, kvs is {}"
                .format(dbname, tb_name, fbytes, fkvs))
        else:
            print(
                "Check failed,DB name is:{},Table name is:{}, f-bytes is {}, f-kvs is {}, t-bytes is {}, t-kvs is {}"
                .format(dbname, tb_name, fbytes, fkvs, tbytes, tkvs))


def check_table(db_name, table_name, tso, mode):
    check_sql = "admin checksum table `{}`".format(table_name)
    set_scan = "set tidb_checksum_table_concurrency = 200"
    set_time = "set tidb_snapshot='{}'".format(tso)
    if mode == "f":
        checksum = mysql_execute("use {}".format(db_name), set_time, set_scan, check_sql)
    else:
        checksum = mysql_execute1("use {}".format(db_name), set_time, set_scan,
                                  check_sql)
    Total_kvs = checksum[0]["Total_kvs"]
    Total_bytes = checksum[0]["Total_bytes"]

    return Total_kvs, Total_bytes


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
                        default="123456")
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
                        default="123456")
    parser.add_argument("-d",
                        dest="database",
                        help="Database name, for example: test, default: None",
                        default="tmp")
    args = parser.parse_args()

    return args


if __name__ == "__main__":
    main()
