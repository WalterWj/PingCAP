#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import MySQLdb
import argparse
import time
import csv
import os
import Queue
import threading

from multiprocessing import Process

try:
    import Queue
except:
    import queue

## If Python is version 2.7, encoding problems can reload sys configuration
try:
    import sys

    reload(sys)
    sys.setdefaultencoding('utf-8')
except:
    pass


def outfile_tidb(mode, file_name, fieldnames, queue):
    while True:
        try:
            _sql = queue.get(True, 1)
            _cmd = mysql_execute(mode, file_name,
                                fieldnames, _sql)
        except:
            print("{} get {}".format(threading.current_thread(), _sql))
            break
        finally:
            print("task is successful~")
        queue.task_done()

def main():
    args = parse_args()
    queue = Queue.Queue()
    get_list_time = time.time()
    id_list = parser_id()
    print("get id cost: {}".format(time.time()-get_list_time))

    if args.column is "all":
        fieldnames = mysql_execute(None, None, None,
                                   "desc {};".format(args.table))
        fieldnames = [i['Field'] for i in fieldnames]
    else:
        fieldnames = str(args.column).split(',')

    batch = int(args.batch)
    for list_id in range(0, len(id_list), batch):
        filter_content = list(id_list[list_id:list_id+batch])
        if len(filter_content) == 1:
            filter_content = filter_content[0]['id']
            _sql = 'select {} from {} where {} = {}'.format(', '.join(
                fieldnames), args.table, args.field, filter_content)
        else:   
            filter_content = str(tuple([i['id'] for i in filter_content]))
            _sql = 'select {} from {} where {} in {}'.format(', '.join(
                fieldnames), args.table, args.field, filter_content)
        queue.put(_sql)

    thread = int(args.thread)
    threads = []
    for num in range(thread):
        file_name = "{}.{}.{}.csv".format(args.database, args.table, num)
        t = threading.Thread(target = outfile_tidb, args = ('csv', file_name, fieldnames, queue))
        threads.append(t)
    
    for num in range(thread):
        threads[num].start()
    
    queue.join()
    # for num in range(thread):
    #     threads[num].join()


def parser_id():
    args = parse_args()
    try:
        schema = mysql_execute(None, None, None, "desc {};".format(args.table))
        id_list = mysql_execute(
            None, None, None,
            "select {} as id from {} {};".format(
                args.field, args.table, args.where))

    except all as error:
        print('Error log is: {}'.format(error))

    return id_list


def mysql_execute(mode=None, file_name=None, fieldnames=[], *_sql):
    args = parse_args()
    host = args.mysql.split(':', 1)[0]
    port = int(args.mysql.split(':', 1)[1])
    try:
        connection = MySQLdb.connect(host=host,
                                     user=args.user,
                                     password=args.password,
                                     port=port,
                                     charset='utf8mb4',
                                     database=args.database)
    except all as error:
        print("Connect Database is failed~\n", error)

    try:
        with connection.cursor(cursorclass=MySQLdb.cursors.SSDictCursor) as cursor:
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
                    content = cursor.fetchall()
                    print("get content cost time is {}".format(time.time() - start_time))
                    writer.writerows(content)
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
                        default="10.0.1.21:4000")
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
                        default="tpch")
    parser.add_argument("-t",
                        dest="table",
                        help="Table name, default: test",
                        default="orders")
    parser.add_argument("-k",
                        dest="field",
                        help="Table primary key, default: _tidb_rowid",
                        default="O_ORDERKEY")
    parser.add_argument("-T",
                        dest="thread",
                        help="Export thread, default: 20",
                        default=20)
    parser.add_argument("-B",
                        dest="batch",
                        help="Export batch size, default: 100000",
                        default=100000)
    parser.add_argument("-w",
                        dest="where",
                        help="Filter condition， for example: where id >= 1, default: null",
                        default="")                
    parser.add_argument(
        "-c",
        dest="column",
        help="Table Column, for example: id,name, default: all",
        default="all")

    args = parser.parse_args()

    return args


if __name__ == "__main__":
    start_time = time.time()
    main()
    end_time = time.time()
    print('Exiting Main Thread, Total cost time is {}'.format(end_time-start_time))
