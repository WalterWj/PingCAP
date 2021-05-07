#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import argparse
import pymysql
import time
import json
import threading


class MyThread(threading.Thread):
    def __init__(self, func, args=()):
        super(MyThread, self).__init__()
        self.func = func
        self.args = args

    def run(self):
        self.result = self.func(*self.args)

    def get_result(self):
        try:
            return self.result
        except Exception:
            return None


def main():
    args = parse_args()
    if args.tables is None:
        db_list = args.database + ","
        dbname = tuple(db_list.split(","))
        tb_sql = "select TABLE_SCHEMA,TABLE_NAME from INFORMATION_SCHEMA.tables where TABLE_SCHEMA in {}".format(
            dbname)
        t_d_list = mysql_execute("f", tb_sql)
    else:
        pass
    tso = mysql_execute("t", "select checkPoint from tidb_binlog.checkpoint")
    tso = json.loads(tso[0]["checkPoint"])
    ftso = tso["ts-map"]["primary-ts"]
    ttso = tso["ts-map"]["secondary-ts"]
    for tb in t_d_list:
        tb_name = tb["TABLE_NAME"]
        dbname = tb["TABLE_SCHEMA"]
        if args.verification == "xor":
            _sql = "select table_name, concat('select bit_xor(CAST(CRC32(concat_ws(',group_concat('`',`COLUMN_NAME`,'`'),', concat(',group_concat('ISNULL(`',`COLUMN_NAME`,'`)'),'))) AS unsigned)) as b_xor from `', table_name, '`') as _sql from `COLUMNS` where TABLE_SCHEMA='{}' and table_name='{}' and data_type not in ('json', 'timestamp') group by table_name".format(
                dbname, tb_name)
            _sql = mysql_execute("f", "use INFORMATION_SCHEMA", _sql)
            bit_xor_sql = _sql[0]["_sql"]
        else:
            bit_xor_sql = "admin checksum table `{}`".format(tb_name)
        start = time.time()
        data = []
        threads = []
        for mod in ["f", "t"]:
            if mod == "f":
                bit_xor = MyThread(check_table,
                                   args=(dbname, bit_xor_sql, ftso, mod))
            else:
                bit_xor = MyThread(check_table,
                                   args=(dbname, bit_xor_sql, ttso, mod))
            threads.append(bit_xor)
            bit_xor.start()
        for t in threads:
            t.join()
            data.append(t.get_result())
        end = time.time()
        f_bit_xor_sum = data[0][1]
        t_bit_xor_sum = data[1][1]
        if args.verification == "xor":
            if f_bit_xor_sum == t_bit_xor_sum:
                print(
                    "Check sucessfull, Cost time is {}s, DB name is: {}, Table name is:{}, bit xor:{}"
                    .format(end - start, dbname, tb_name, f_bit_xor_sum))
            else:
                print(
                    "Check failed, Cost time is {}s, DB name is:{},Table name is:{}, f-bit_xor is:{}, t-bit_xor is:{}"
                    .format(end - start, dbname, tb_name, f_bit_xor_sum,
                            t_bit_xor_sum))
        else:
            if f_bit_xor_sum == t_bit_xor_sum:
                print(
                    "Check successful, Cost time is {}s, DB name is:{}, Table name is:{}, kvs is {}"
                    .format(end - start, dbname, tb_name, f_bit_xor_sum))
            else:
                print(
                    "Check failed, Cost time is {}s, DB name is:{},Table name is:{}, f-kvs is {}, t-kvs is {}"
                    .format(end - start, dbname, tb_name, f_bit_xor_sum,
                            t_bit_xor_sum))


def check_table(db_name, bit_xor_sql, tso, mode):
    args = parse_args()
    # tso = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    set_engine = "set tidb_isolation_read_engines='tikv, tidb';"
    set_scan = "set tidb_distsql_scan_concurrency = {}".format(args.thread)
    set_time = "set tidb_snapshot='{}'".format(tso)
    _mode = args.mode.split(',', 1)
    if mode == "f" and _mode[0].strip() == "tidb":
        content = mysql_execute(mode, "use {}".format(db_name), set_time,
                                set_scan, set_engine, bit_xor_sql)
    elif mode == "f" and _mode[0].strip() == "mysql":
        content = mysql_execute(mode, "use {}".format(db_name), bit_xor_sql)
    elif mode == "t" and _mode[1].strip() == "tidb":
        content = mysql_execute(mode, "use {}".format(db_name), set_time,
                                set_scan, set_engine, bit_xor_sql)
    elif mode == "t" and _mode[1].strip() == "mysql":
        content = mysql_execute(mode, "use {}".format(db_name), bit_xor_sql)
    else:
        print("unknown~")
    if args.verification == "xor":
        _result = content[0]["b_xor"]
    else:
        _result = content[0]["Total_kvs"]

    return mode, _result


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
        help="Source database address and port, default: 127.0.0.1:4000",
        default="127.0.0.1:4000")
    parser.add_argument("-uf",
                        dest="fuser",
                        help="Source database account, default: root",
                        default="root")
    parser.add_argument("-pf",
                        dest="fpassword",
                        help="Source database password, default: null",
                        default="123456")
    parser.add_argument(
        "-ht",
        dest="tmysql",
        help="Target database address and port, default: 127.0.0.1:4000",
        default="127.0.0.1:4000")
    parser.add_argument("-ut",
                        dest="tuser",
                        help="Target database account, default: root",
                        default="root")
    parser.add_argument("-pt",
                        dest="tpassword",
                        help="Target database password, default: null",
                        default="123456")
    parser.add_argument(
        "-d",
        dest="database",
        help="Database name, for example: test,tmp, default: None",
        default="tmp,tmp1")
    parser.add_argument(
        "-t",
        dest="tables",
        help="Table name, for example: tmp.t,tmp.t1, default: None",
        default=None)
    parser.add_argument(
        "-T",
        dest="thread",
        help=
        "set tidb_distsql_scan_concurrency, for example: 200, default: 200",
        default=200)
    parser.add_argument(
        "-m",
        dest="mode",
        help=
        "Compare database types, for example: tidb,mysql, default: tidb,tidb",
        default="tidb,tidb")
    parser.add_argument(
        "-v",
        dest="verification",
        help="Verification method, for example: checksum, default: xor",
        default="xor")

    args = parser.parse_args()

    return args


if __name__ == "__main__":
    main()
