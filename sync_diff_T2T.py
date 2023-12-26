#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import argparse  # 导入用于解析命令行参数的模块
import json  # 导入用于处理JSON数据的模块
import pymysql  # 导入用于操作MySQL数据库的模块
import os  # 导入用于处理文件和目录路径的模块
import shlex  # 导入用于解析字符串为命令的模块
import subprocess  # 导入用于执行外部命令的模块
from datetime import datetime  # 导入处理日期和时间的模块
import sys  # 导入用于与Python解释器交互的模块

def main():
    # 获取当前脚本的绝对路径
    script_path = os.path.abspath(__file__)

    # 输出当前脚本的绝对路径
    print("当前脚本的绝对路径:", script_path)
    script_directory = os.path.dirname(script_path)
    
    args = parse_args()  # 解析命令行参数并存储在args变量中
    # 获取上下游 tso mapping
    masterTso, slaveTso = parseTso(args.slaveHost, args.slaveUser, args.slavePassword)  # 解析上下游数据库的时间戳信息
    # 生成配置文件
    # 获取当前时间
    current_time = datetime.now()
    # 格式化时间为精确到秒的字符串
    formatted_time = current_time.strftime("%Y%m%d%H%M%S")
    outDir = os.path.join(script_directory, formatted_time)  # 构建输出目录路径
    # 格式化库列表
    if len(args.DatabaseList) > 0:
        dbList = ['"{}.*"'.format(db) for db in args.DatabaseList.split(',')]
        dbList = ",".join(dbList)
    else:
        dbList = ""
    
    # 生成配置
    formatConfig(args.threadCount, args.masterHost, args.masterUser, args.masterPassword, masterTso, args.slaveHost, args.slaveUser, args.slavePassword, slaveTso, outDir, dbList)  # 生成配置文件
    
    # 执行命令
    binaryPath = os.path.join(args.binaryPath, "sync_diff_inspector")
    command = "{} --config=./config.toml".format(binaryPath)  # 构建执行命令
    # 命令 print
    print("执行命令：{}".format(command))
    # update gc: changeGc("127.0.0.1:4100", "root", "root", "12h")
    print("update gc for master")
    masterGcTime = changeGc(args.masterHost, args.masterUser, args.masterPassword, args.gcTime)
    print("update gc for slave")
    slaveGcTime = changeGc(args.slaveHost, args.slaveUser, args.slavePassword,args.gcTime)
    try:
        result = subprocess.check_output(shlex.split(command))  # 执行命令并捕获输出
        print("执行结果:", result)
    except subprocess.CalledProcessError as e:
        print(e.output.decode('utf-8'))
        # Change back to gc time
        print("diff Error, Change back to gc time")
        print("update gc for master")
        changeGc(args.masterHost, args.masterUser, args.masterPassword, masterGcTime)
        print("update gc for slave")
        changeGc(args.slaveHost, args.slaveUser, args.slavePassword,slaveGcTime)
        exit(1)
    
    # Change back to gc time
    print("update gc for master")
    changeGc(args.masterHost, args.masterUser, args.masterPassword, masterGcTime)
    print("update gc for slave")
    changeGc(args.slaveHost, args.slaveUser, args.slavePassword,slaveGcTime)

def formatConfig(threadCount, masterHost, masterUser, masterPassword, masterTso, slaveHost, slaveUser, slavePassword, slaveTso, outDir, dbList):
    masterPort = int(masterHost.split(":",1)[1])
    slavePort = int(slaveHost.split(":",1)[1])
    config = """
# Diff Configuration.

######################### Global config #########################

# how many goroutines are created to check data
check-thread-count = {}

# set false if just want compare data by checksum, will skip select data when checksum is not equal.
# set true if want compare all different rows, will slow down the total compare time.
export-fix-sql = true

# ignore check table's data
check-struct-only = false

######################### Databases config #########################
[data-sources]
[data-sources.master]
    host = "{}"
    port = {}
    user = "{}"
    password = "{}"
    snapshot = "{}"

[data-sources.slave]
    host = "{}"
    port = {}
    user = "{}"
    password = "{}"
    snapshot = "{}"

######################### Task config #########################
# Required
[task]
    # 1 fix sql: fix-target-TIDB1.sql
    # 2 log: sync-diff.log
    # 3 summary: summary.txt
    # 4 checkpoint: a dir
    output-dir = "{}"

    source-instances = ["master"]

    target-instance = "slave"
    target-check-tables = ["!INFORMATION_SCHEMA.*","!METRICS_SCHEMA.*","!PERFORMANCE_SCHEMA.*","!mysql.*","!test.*","!tidb_binlog.*",{}]

    """.format(threadCount, masterHost.split(":",1)[0], masterPort, masterUser, masterPassword, masterTso, 
               slaveHost.split(":",1)[0], slavePort, slaveUser, slavePassword, slaveTso, outDir, dbList)
    
    # 打开文件以写入内容，如果文件不存在则创建它
    with open('config.toml', 'w') as file:
        file.write("{}\n".format(config))
        
        # 你可以继续写入更多内容
    file.close()
    
    return config

def parseTso(slaveHost, slaveUser, slavePassword):
    port = int(slaveHost.split(":",1)[1])
    # connect mysql
    config = {
        "host": slaveHost.split(":",1)[0],
        "user": slaveUser,
        "password": slavePassword,
        "port": port,
        "charset": 'utf8mb4',
        "cursorclass": pymysql.cursors.DictCursor
    }

    connection = pymysql.connect(**config)  # 连接到MySQL数据库
    cursor = connection.cursor()
    
    sql = """
    select checkPoint from tidb_binlog.checkpoint;
    """
    cursor.execute(sql)  # 执行SQL查询
    content = cursor.fetchall()
    connection.commit()
    connection.close()
    content = content[0]['checkPoint']
    content = json.loads(content)
    masterTso = content['ts-map']['primary-ts']
    slaveTso = content['ts-map']['secondary-ts']

    return masterTso, slaveTso

def changeGc(dbHost, dbUser, dbPassword, gcTime):
    port = int(dbHost.split(":",1)[1])
    # connect mysql
    config = {
        "host": dbHost.split(":",1)[0],
        "user": dbUser,
        "password": dbPassword,
        "port": port,
        "charset": 'utf8mb4',
        "cursorclass": pymysql.cursors.DictCursor
    }

    connection = pymysql.connect(**config)  # 连接到MySQL数据库
    cursor = connection.cursor()
    # select gc time sql
    selectGcSql = """
    select variable_value from mysql.tidb where variable_name='tikv_gc_life_time'; 
    """
    # update gc time sql
    upGcSql = """
    update mysql.tidb set VARIABLE_VALUE='{}' where variable_name='tikv_gc_life_time';
    """.format(gcTime)
    # select gc time
    cursor.execute(selectGcSql)
    selectGc = cursor.fetchone()
    # update gc time to gcTime
    cursor.execute(upGcSql)
    connection.commit()
    connection.close()
    print("TiDB gc: {}, update gc: {}".format(selectGc['variable_value'], gcTime))
    
    # return tidb gc time
    return selectGc['variable_value']

# 解析命令行参数
def parse_args():
    parser = argparse.ArgumentParser(description="Check tables for TiDB to TiDB.")
    parser.add_argument(
        "-mh",
        dest="masterHost",
        help="Source database address and port, default: 127.0.0.1:4000",
        default="127.0.0.1:4000")
    parser.add_argument("-mu",
                        dest="masterUser",
                        help="Source database account, default: root",
                        default="root")
    parser.add_argument("-mp",
                        dest="masterPassword",
                        help="Source database password, default: null",
                        default="")
    parser.add_argument("-dl",
                        dest="DatabaseList",
                        help="Diff database list, default: null, for example: db1,db2,db3",
                        default="")
    parser.add_argument(
        "-sh",
        dest="slaveHost",
        help="Target database address and port, default: 127.0.0.1:4000",
        default="127.0.0.1:4000")
    parser.add_argument("-su",
                        dest="slaveUser",
                        help="Target database account, default: root",
                        default="root")
    parser.add_argument("-sp",
                        dest="slavePassword",
                        help="Target database password, default: null",
                        default="tidb@123")
    parser.add_argument(
        "-b",
        dest="binaryPath",
        help="Sync diff binary path, for example: /user/bin/, default: ./",
        default="./")
    parser.add_argument(
        "-t",
        dest="threadCount",
        help="set check-thread-count, default: 16",
        default="16")
    parser.add_argument(
        "-g",
        dest="gcTime",
        help="set tidb gc time, default: 24h",
        default="24h")

    args = parser.parse_args()

    return args

if __name__ == "__main__":
    main()
    