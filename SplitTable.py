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

        return content

    def keys(self, db, table):
        # sql
        sql = '''
        select
            INDEX_ID,
            INDEX_NAME,
            tidb_decode_key(start_key) start,
            tidb_decode_key(END_KEY) end
        from
            information_schema.tikv_region_status
        where
            DB_NAME = '{}'
            and TABLE_NAME = '{}'
        order by
            INDEX_ID;
        '''.format(db, table)
        keys = self.mysqlconnect(sql)

        return keys

    def parserkeys(self, ct):
        try:
            sct = eval(ct['start'])
        except:
            sct = {}
        if sct.has_key('_tidb_rowid'):
            sctv = []
            sctv.append(sct['_tidb_rowid'])
            sctv = tuple(sctv)
        elif sct.has_key('handle') and ct['INDEX_NAME'] is None:
            sctv = sct['handle'].values()
            sctv = tuple(sctv[::-1])
        elif sct.has_key('index_vals') and ct['INDEX_ID'] == sct['index_id']:
            sctv = sct['index_vals'].values()
            sctv = tuple(sctv[::-1])
        else:
            sctv = None

        try:
            ect = eval(ct['end'])
        except:
            ect = {}
        if ect.has_key('_tidb_rowid'):
            ectv = []
            ectv.append(ect['_tidb_rowid'])
            ectv = tuple(ectv)
        elif ect.has_key('handle') and ct['INDEX_NAME'] is None:
            ectv = ect['handle'].values()
            ectv = tuple(ectv[::-1])
        elif ect.has_key('index_vals') and ct['INDEX_ID'] == ect['index_id']:
            ectv = ect['index_vals'].values()
            ectv = tuple(ectv[::-1])
        else:
            ectv = None

        if ectv is None and sctv is None:
            allct = ''
        elif ectv is None:
            if len(sctv) == 1:
                sctv = str(sctv).replace(',', '')
            allct = str(sctv)
        elif sctv is None:
            if len(ectv) == 1:
                ectv = str(ectv).replace(',', '')
            allct = str(ectv)
        else:
            if len(sctv) == 1:
                sctv = str(sctv).replace(',', '')
            if len(ectv) == 1:
                ectv = str(ectv).replace(',', '')
            allct = str(sctv) + ',' + str(ectv)
            
        allct = allct.strip(',')
        
        type = ct['INDEX_NAME']

        return type, allct
    
    def parserSql(self, db, tbl, ct):
        for type, val in ct.items():
            sql = ''
            val = val.strip(',')
            if type == 'None' or type == 'handle':
                if val is not '':
                    sql = 'split table `{}`.`{}` by {};'.format(db, tbl, val)
            else:
                if val is not '':
                    sql = 'split table `{}`.`{}` index `{}` by {};'.format(db, tbl, type, val)
            
            print(sql)
        
        return sql

    def main(self):
        args = self.parse_args()

        db = args.tables.split('.')[0]
        tb = args.tables.split('.')[1]
        keys = self.keys(db, tb)
        parsers = {}
        for key in keys:
            type, ct = self.parserkeys(key)
            type = str(type)
            parsers[type] = ct + ',' + parsers.get(type,'')
        
        if args.totables is '':
            self.parserSql(db, tb, parsers)
        else:
            tdb = args.totables.split('.')[0]
            ttb = args.totables.split('.')[1]
            
            self.parserSql(tdb, ttb, parsers)

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
                            default="")
        parser.add_argument(
            "-t",
            dest="tables",
            help=
            "Table name (database.table), for example: test.test default: None",
            default='')
        parser.add_argument(
            "-tt",
            dest="totables",
            help=
            "Table name (database.table), for example: test.test1 default: None",
            default='')

        args = parser.parse_args()

        return args


if __name__ == "__main__":
    main = SplitTable()
    main.main()
