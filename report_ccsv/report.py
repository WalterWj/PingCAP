#!/usr/bin/env python
# coding: utf-8

import requests
import argparse
import csv
from datetime import datetime, timedelta

def main():
    args = parse_args()
    # 读取参数文件
    file_path = 'query.lst'
    parameters = []

    with open(file_path, 'r') as file:
        lines = file.readlines()

        # 遍历每一行，解析参数
        for line in lines:
            parts = line.split('|@|')
            if len(parts) == 3:
                parameters.append({
                    'percentile': parts[0].strip(),
                    'query': parts[1].strip(),
                    'unit': parts[2].strip()
                })
        file.close()
    
    # 读取时间文件
    file_path = 'time.lst'
    time_list = []

    with open(file_path, 'r') as file:
        lines = file.readlines()

        # 遍历每一行，将时间字符串添加到列表中
        for line in lines:
            time_list.append(line.strip())  # 去除换行符并添加到列表
        file.close()

    # print(parameters)
    url = args.plhost
    # query = '''
    # histogram_quantile(0.99, sum(rate(tidb_server_handle_query_duration_seconds_bucket[2h])) by (le)) * 1000
    # '''  # 替换为你的PromQL查询语句
    # time_str='2023-11-18T19:00:00.000Z'
    ct_list = {}
    for time_str in time_list:
        time_str = "{}T{}Z".format(args.date ,time_str)
        # values = execute_query(url, query, time_str)
        # print(values)
        for parameter in parameters:    
            query = parameter['query']
            percentile = parameter['percentile']
            unit = parameter['unit']
            values = execute_query(url, query, time_str)
            # print("Time:{}: 指标：{},values:{}{}".format(time_str, percentile, values, unit)) 
            if percentile in ct_list: 
                ct_list[percentile] = ct_list[percentile] + "|@|" + values + unit
            else:
                ct_list[percentile] = values + unit

    with open('data.csv', 'w', newline='') as csvfile:
        for key, ct in ct_list.items():
            data = key + "|@|" + ct
            data_list = data.split('|@|')
            writer = csv.writer(csvfile)
            writer.writerow(data_list)
    
    print("all sucessfull")

def parse_args():
    # 创建 ArgumentParser 对象
    parser = argparse.ArgumentParser(description='')
    # 添加命令行参数
    parser.add_argument('--plhost', '-H', type=str, default='127.0.0.1:9090', help='prometheus host:port')
    parser.add_argument('--date', '-dt', type=str, default="2023-11-19", help='date time: 2023-11-19')
    # 解析命令行参数
    args = parser.parse_args()
    return args

"""
Prometheus API
输入：
  API IP address and port
  query
  time
  
返回：
  结果
"""
def execute_query(url, query, time_str):
    prometheus_url = "http://{}".format(url)  # 替换为你的Prometheus实例的URL
    # query = '''
    # histogram_quantile(0.99, sum(rate(tidb_server_handle_query_duration_seconds_bucket[2h])) by (le)) * 1000
    # '''  # 替换为你的PromQL查询语句

    # 构建Prometheus查询API的URL
    api_url = f"{prometheus_url}/api/v1/query?query={query}"
    # time_str='2023-11-18T19:00:00.000Z'
    # 解析时间字符串为datetime对象（假设该时间是UTC时间）
    time = datetime.strptime(time_str, "%Y-%m-%dT%H:%M:%S.%fZ")
    # 将时间标记为UTC时区
    time = time - timedelta(hours=8)

    # 转换为字符串格式
    result_time_str = time.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    
    api_url = api_url + '&time=' + result_time_str
    
    # 发送GET请求获取查询结果
    response = requests.get(api_url)

    # 检查响应状态码
    if response.status_code == 200:
        result = response.json()  # 获取JSON格式的结果
        # print(result)  # 处理查询结果，这里打印结果
        # print('99 duration 为 {} ms'.format(result['data']['result'][0]['value'][1]))
    else:
        print(f"Failed to execute query. Status code: {response.status_code}")
    
    try:    
        rt = result['data']['result'][0]['value'][1]
        rt = round(float(rt), 2)
        rt = str(rt)
    except Exception as e:
        rt = "-"
    
    return rt



if __name__ == "__main__":
    # execute_query()
    main()
