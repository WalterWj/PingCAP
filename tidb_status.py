#!/usr/bin/env python
# -*- coding: UTF-8 -*-


import subprocess, os
import time, argparse


def main():
    args = parse_args()
    httpApi = "http://{}:{}/status".format(args.host, args.status)
    dropPort = "sudo iptables -A INPUT -p tcp --dport {} -j DROP".format(args.port)
    acceptPort = "sudo iptables -D INPUT -p tcp --dport {} -j DROP".format(args.port)
    portStatus = "sudo iptables -L -n | grep {} | grep DROP| wc -l".format(args.port)
    psStatus = "sudo ps aux |grep tidb-server | grep {}|grep -Ev grep|wc -l".format(args.port)
    while True:
        print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
        time.sleep(args.time)
        if checkPs(psStatus):
            if checkApi(httpApi, args.number):
                if checkPs(portStatus):
                    os.system(acceptPort)
                    print("开启端口 {}".format(args.port))
                else:
                    print("端口 {} 已经开启".format(args.port))
            else:
                if checkPs(portStatus):
                    print("端口 {} 已经关闭".format(args.port))
                else:
                    os.system(dropPort)
                    print("关闭端口 {}".format(args.port))
        else:
            print("tidb 数据库进程不存在, 端口为：{}".format(args.port))


def checkApi(httpApi, number):
    tidbA = tidbActive(httpApi)
    nc = 0
    while True:
        if tidbA:
            print("数据库状态正常")
            rt = True
            break
        else:
            nc += 1

        if nc >= number:
            rt = False
            break
        else:
            print("第 {} 次检测不正常".format(nc))

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
                        dest="time",
                        help="sleep time, default: 3",
                        default=3)
    args = parser.parse_args()

    return args


if __name__ == "__main__":
    main()
