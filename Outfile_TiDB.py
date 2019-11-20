#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import pymysql
import argparse
import threading
import time
import csv
import os
import queue

## If Python is version 2.7, encoding problems can reload sys configuration
# import sys

# reload(sys)
# sys.setdefaultencoding('utf-8')

queue = queue.Queue()
# lock = threading.Lock()

class outfile_tidb(threading.Thread):
    def __init__(self, mode, file_name, fieldnames, queue):
        threading.Thread.__init__(self)
        self.mode = mode
        self.file_name = file_name
        self.fieldnames = fieldnames
        self.queue = queue

    def run(self):
        while True:
            _sql = self.queue.get()
            if _sql is None:
                break

            try:
                _cmd = mysql_execute(self.mode, self.file_name, self.fieldnames, _sql)
                # lock.acquire()
                print("Retrieved", _sql)
                time.sleep(1)
                # print('===========')
                # lock.release()
            except Exception as error:
                print("Error is {}".format(error))
            finally:
                self.queue.task_done()

def main():
    args = parse_args()
    max_id, min_id = parser_id()
    if args.column is "all":
        fieldnames = mysql_execute(None, None, None, "desc {};".format(args.table))
        fieldnames = [i['Field'] for i in fieldnames]
    else:
        fieldnames = str(args.column).split(',')

    thread = int(args.thread)
    for num in range(thread):
        file_name = "{}.{}.{}.csv".format(args.database, args.table, num)
        t = outfile_tidb('csv', file_name, fieldnames,queue)
        t.setDaemon(True)
        t.start()

    batch = int(args.batch)
    for _id in range(min_id, max_id, batch):
        _sql = 'select {} from {} where {} >= {} and {} < {}'.format(', '.join(fieldnames), args.table, args.field, _id, args.field, _id+batch)
        # print(_sql)
        queue.put(_sql)

    queue.join()
        
def parser_id():
    args = parse_args()
    try:
        schema = mysql_execute(None, None, None, "desc {};".format(args.table))
        content = mysql_execute(None, None, None, "select min({}) as min_id, max({}) as max_id from {};".format(args.field, args.field, args.table))
        if content[0]['max_id'] is not None:
            max_id = content[0]['max_id'] + 1
            min_id = content[0]['min_id']
        else:
            max_id = 0
            min_id = 0          
    except all as error:
        print('Error log is: {}'.format(error))

    return max_id, min_id


def mysql_execute(mode=None, file_name=None, fieldnames=[], *_sql):
    args = parse_args()
    host = args.mysql.split(':', 1)[0]
    port = int(args.mysql.split(':', 1)[1])
    try:
        connection = pymysql.connect(host=host,
                                     user=args.user,
                                     password=args.password,
                                     port=port,
                                     charset='utf8mb4',
                                     database=args.database,
                                     cursorclass=pymysql.cursors.DictCursor)
    except all as error:
        print("Connect Database is failed~\n", error)

    try:
        with connection.cursor() as cursor:
            cursor.execute("SET NAMES utf8mb4")
            for sql in _sql:
                cursor.execute(sql)

            if mode is not 'csv':
                content = cursor.fetchall()
            else:
                start_time = time.time()
                with open(file_name, 'a+') as csvfile:
                    writer = csv.DictWriter(csvfile,
                                            fieldnames=fieldnames,
                                            quoting=csv.QUOTE_NONNUMERIC)
                    if os.path.getsize(file_name):
                        pass
                    else:
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
                _sql))

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
    parser.add_argument("-k",
                        dest="field",
                        help="Table primary key, default: _tidb_rowid",
                        default="_tidb_rowid")
    parser.add_argument("-T",
                        dest="thread",
                        help="Export thread, default: 20",
                        default=20)
    parser.add_argument("-B",
                        dest="batch",
                        help="Export batch size, default: 100000",
                        default=100000)
    parser.add_argument(
        "-c",
        dest="column",
        help="Table Column, for example: id,name, default: all",
        default="all")

    args = parser.parse_args()

    return args


if __name__ == "__main__":
    main()
    print('Exiting Main Thread')
