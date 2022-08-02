#!/usr/bin/env python
# -*- coding: UTF-8 -*-

# import subprocess
import os
import time
import argparse
import requests
import json


def main():
    args = parse_args()
    while True:
        # 异常下尝试重试次数
        num = 3
        # 获取 tiflash 状态
        stat = wileStatus(args.promAddr, args.flashAddr, num)
        if stat == num:
            content = "tiflash 是否重启，已经连续判断 {} 次，进行 tidb-server 重启".format(num)
            logsFile(content)
            # 数据库重启
            rt_tidb(args.tidbPort)
            # 重启后等待一定时间进入下个轮回
            time.sleep(300)
        else:
            pass

        # 固定时间轮询
        time.sleep(7)


def rt_tidb(port):
    # 根据端口拼 service 文件名
    serviceFileName = "tidb-{}.service".format(port)
    command = "sudo systemctl restart {}".format(serviceFileName)
    try:
        os.system(command)
        content = "重启 tidb 成功：{}".format(command)
        logsFile(content)
    except all:
        logsFile("重启异常: {}".format(all))


def wileStatus(promAddr, flashAddr, num=3):
    wc = 0
    while wc < num:
        # 如果发现 tiflash 异常，默认进行 3 次重取操作
        stat = tiflashStatus(promAddr, flashAddr)
        # print("断点: {}".format(stat))
        if stat == 0:
            # 状态为 0，代表 tiflash 正常
            content = "tiflash 状态正常：{} {}".format(promAddr, stat)
            logsFile(content)
            return True
        elif stat == 1:
            wc += 1
            content = "tiflash 可能发生重启：{} {}，开始多次判断：第 {} 次".format(
                promAddr, stat, wc)
            logsFile(content)
            # 等待一定时间重新获取 tiflash 状态
            time.sleep(3)
        else:
            logsFile("其他情况，stat 为：{}".format(stat))
            break

    return wc


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


def tiflashStatus(promAddr, flashAddr):
    # 5min 内发现 tiflash 重启
    cT = 5
    promeQuery = "changes(tiflash_proxy_process_start_time_seconds{instance='%s',job='tiflash'}[%sm])" % (
        flashAddr, cT)
    stat = checkProm(promAddr, promeQuery)
    stat = json.loads(stat)
    # 从结果取出结果 0 或者 1
    dataLen = len(stat['data']['result'])
    if dataLen == 0:
        logsFile("tiflash 是否重启无法捕获，tiflash 可能超过 {}min 未启动。stat 状态为：{}".format(
            cT, stat))
    else:
        status = int(stat['data']['result'][0]['value'][1])

    return status


def checkProm(prometheus_address, query):
    # 请求 Prometheus 执行 Prometheus query，返回结果
    try:
        response = requests.get('http://%s/api/v1/query' % prometheus_address,
                                params={
                                    'query': query
                                }).text
        return response
    except all:
        logsFile("访问 Prometheus 异常", all)
        return None


def parse_args():
    # Incoming parameters
    parser = argparse.ArgumentParser(
        description="如果 tiflash 重启，重启本地 tidb-server")
    parser.add_argument("-P",
                        dest="tidbPort",
                        help="tidb port, default: 4000",
                        default=4000)
    parser.add_argument("-ph",
                        dest="promAddr",
                        help="Prometheus ip 和端口, default: 127.0.0.1:9090",
                        default="127.0.0.1:9090")
    parser.add_argument(
        "-th",
        dest="flashAddr",
        help="tiflash ip 和 proxy status 端口, default: 127.0.0.1:20292",
        default="127.0.0.1:20292")

    args = parser.parse_args()

    return args


if __name__ == "__main__":
    main()
