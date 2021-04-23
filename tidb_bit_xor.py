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
    t_table = mysql_execute("f", u_dbname, t_sql)
    tso = mysql_execute("t", "select checkPoint from tidb_binlog.checkpoint")
    tso = json.loads(tso[0]["checkPoint"])
    ftso = tso["ts-map"]["primary-ts"]
    ttso = tso["ts-map"]["secondary-ts"]
    for tb in t_table:
        tb_name = tb["Tables_in_{}".format(dbname)]
        _sql = "select table_name, concat('select bit_xor(CAST(CRC32(concat_ws(',group_concat('`',`COLUMN_NAME`,'`'),', concat(',group_concat('ISNULL(`',`COLUMN_NAME`,'`)'),'))) AS unsigned)) as b_xor from ', table_name) as _sql from `COLUMNS` where TABLE_SCHEMA='{}' and table_name='{}' and data_type != 'json' group by table_name".format(
            dbname, tb_name)
        _sql = mysql_execute("f", "use INFORMATION_SCHEMA", _sql)
        bit_xor_sql = _sql[0]["_sql"]
        start = time.time()
        f_bit_xor = check_table(dbname, bit_xor_sql, ftso, "f")
        t_bit_xor = check_table(dbname, bit_xor_sql, ttso, "t")
        end = time.time()
        if f_bit_xor == t_bit_xor:
            print(
                "Check sucessfull, Cost time is {}, DB name is: {}, Table name is:{}, bit xor:{}"
                .format(end - start, dbname, tb_name, f_bit_xor))
        else:
            print(
                "Check failed, Cost time is {}, DB name is:{},Table name is:{}, f-bit_xor is:{}, t-bit_xor is:{}"
                .format(end - start, dbname, tb_name, f_bit_xor, t_bit_xor))


def check_table(db_name, bit_xor_sql, tso, mode):
    set_scan = "set tidb_distsql_scan_concurrency = 200"
    set_time = "set tidb_snapshot='{}'".format(tso)
    if mode == "f":
        bit_xor = mysql_execute("f", "use {}".format(db_name), set_time,
                                set_scan, bit_xor_sql)
    else:
        bit_xor = mysql_execute("t", "use {}".format(db_name), set_time,
                                set_scan, bit_xor_sql)
    bit_xor = bit_xor[0]["b_xor"]

    return bit_xor


def mysql_execute(mode, *_sql):
    # connect mysql
    args = parse_args()
    if mode == 'f':
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
    else:
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
    cursor.execute("set group_concat_max_len=10240000")
    cursor.execute("set tidb_isolation_read_engines='tikv, tidb';")
    for sql in _sql:
        cursor.execute(sql)
        content = cursor.fetchall()
        connection.commit()
    connection.close()

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
