#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import argparse
import pymysql

# If Python is version 2.7, encoding problems can reload sys configuration
try:
    import sys
    import os

    reload(sys)
    sys.setdefaultencoding('utf-8')
except:
    pass


class SplitTable():

    def __init__(self):
        args = self.parse_args()
        # db config
        self.config = {
            "host": args.mysql,
            "port": int(args.port),
            "user": args.user,
            "password": args.password,
            "charset": 'utf8mb4',
            "cursorclass": pymysql.cursors.DictCursor
        }

    def mysqlconnect(self, *_sql):
        connection = pymysql.connect(**self.config)
        # with connection.cursor() as cursor:
        cursor = connection.cursor()
        for sql in _sql:
            cursor.execute(sql)
        content = cursor.fetchall()
        connection.commit()
        cursor.close()
        connection.close()

        print(content)
        return content

    def tableSplit(self):
        pass

    def indexSplit(self):
        pass

    def parse_args(self):
        # Incoming parameters
        parser = argparse.ArgumentParser(
            description="Update table statistics manually")
        parser.add_argument("-P",
                            dest="port",
                            help="tidb port, default: 4000",
                            default=4201)
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
                            default="tidb@123")
        parser.add_argument(
            "-d",
            dest="database",
            help="Database name, for example: test,test1, default: None",
            default=None)
        parser.add_argument(
            "-t",
            dest="tables",
            help=
            "Table name (database.table), for example: test.test,test.test2, default: None",
            default=None)
        parser.add_argument(
            "-sh",
            dest="stats_healthy",
            help=
            "Table stats healthy, If it is below the threshold, then analyze~",
            default=100)

        args = parser.parse_args()

        return args


if __name__ == "__main__":
    main = SplitTable()
    _sql = '''
    select
	*,
	start_key,
	tidb_decode_key(start_key) b,
	END_KEY ,
	tidb_decode_key(END_KEY) b
from
	information_schema.tikv_region_status
where
	DB_NAME = 'test'
	and TABLE_NAME = 'sbt2'
	order by INDEX_ID ;
    '''
    main.mysqlconnect(_sql)
