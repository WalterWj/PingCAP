#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import subprocess
import os
import time
import argparse


def main():
    args = parse_args()
    httpApi = "http://{}:{}/status".format(args.host, args.status)
    dropPort = "sudo iptables -A INPUT -p tcp --dport {} -j REJECT --reject-with tcp-reset".format(
        args.port)
    acceptPort = "sudo iptables -D INPUT -p tcp --dport {} -j REJECT --reject-with tcp-reset".format(
        args.port)
    portStatus = "sudo iptables -L -n | grep {} | grep reject| wc -l".format(
        args.port)
    psStatus = "sudo ps aux |grep tidb-server | grep {}|grep -Ev grep|wc -l".format(
        args.port)
    while True:
        time.sleep(int(args.Stime))
        if checkPs(psStatus):
            if checkApi(httpApi, args.number):
                if checkPs(portStatus):
                    # 等待 10s 后恢复
                    time.sleep(10)
                    os.system(acceptPort)
                    logsFile("开启端口 {}".format(args.port))
                else:
                    logsFile("端口 {} 已经开启".format(args.port))
            else:
                if checkPs(portStatus):
                    logsFile("端口 {} 已经关闭".format(args.port))
                else:
                    # 避免在检测过程中，tidb-server 进程关闭
                    if checkPs(psStatus):
                        os.system(dropPort)
                        logsFile("关闭端口 {}".format(args.port))
                    else:
                        logsFile("tidb 数据库进程不存在, 端口为：{}".format(args.port))
        else:
            logsFile("tidb 数据库进程不存在, 端口为：{}".format(args.port))


def checkApi(httpApi, number):
    nc = 0
    while True:
        # 判断 api 状态是否异常
        tidbA = tidbActive(httpApi)
        if tidbA:
            logsFile("数据库状态正常")
            rt = True
            break
        else:
            nc += 1
        # 控制异常次数，默认连续 3 次才进行关闭
        if nc >= number:
            rt = False
            logsFile("第 {} 次检测不正常".format(nc))
            break
        else:
            logsFile("第 {} 次检测不正常".format(nc))

        time.sleep(1)

    return rt


def checkPs(command):
    sta = os.popen(command)
    sta = int(sta.read())
    if sta != 0:
        rt = True
    else:
        rt = False

    return rt


def tidbStatus(portStatus):
    sta = os.popen(portStatus)
    sta = int(sta.read())

    return sta


def tidbActive(httpApi):
    try:
        subprocess.check_output(["curl", "-slm", "1", httpApi])
        rt = True
    except Exception:
        rt = False

    return rt


def logsFile(content):
    fileName = time.strftime("%Y-%m-%d", time.localtime()) + "-status.log"
    dirs = "logs"
    # 判断有没有 logs 目录，如果没有就创建一个
    if not os.path.exists(dirs):
        os.makedirs(dirs)
    # 日志文件添加 logs 目录
    fileName = os.path.join(dirs, fileName)
    timeLocal = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    with open(fileName, "a+") as f:
        f.write("{}: {} \n".format(timeLocal, content))


def parse_args():
    # Incoming parameters
    parser = argparse.ArgumentParser(description="Check tidb status")
    parser.add_argument("-P",
                        dest="port",
                        help="tidb port, default: 4000",
                        default=4000)
    parser.add_argument("-H",
                        dest="host",
                        help="Database address, default: 127.0.0.1",
                        default="127.0.0.1")
    parser.add_argument("-s",
                        dest="status",
                        help="TiDB status port, default: 10080",
                        default="10080")
    parser.add_argument("-n",
                        dest="number",
                        help="try number, default: 3",
                        default=3)
    parser.add_argument("-t",
                        dest="Stime",
                        help="sleep time, default: 3",
                        default=3)

    args = parser.parse_args()

    return args


if __name__ == "__main__":
    main()
