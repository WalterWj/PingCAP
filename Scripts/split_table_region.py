#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import json
import argparse
import shlex
import subprocess

def main():
    pass

def table_region():
    args = parse_args()
    httpAPI = "http://{}/tables/{}/{}/regions".format(args.tidb, args.port, args.database, args.table)

    webContent = subprocess.check_output(["curl", "-sl", httpAPI])
    region_info = json.loads(webContent)
    table_id = region_info['id']
    region_id = []
    index_region_id = []
    index_name = []
    for regions in region_info['record_regions']:
        region_id.append(regions["region_id"])
    if region_info['indices'] is not None:
        for regions in region_info['indices']:
            index_region_id.append(regions['id'])
            index_name.append(regions['name'])
            
            for store_id in regions['regions']:
                
                print('Index name is {}, and leader store id is {}').format(regions['name'], region['regions'][])

def Split_region(region_id):
    args = parse_args()
    _split_cmd = "../resources/bin/pd-ctl -u http://{} -d operator add split-region {} --policy=approximate".format(
        args.pd, region_id)
    try:
        _sc = subprocess.check_output(shlex.split(_split_cmd))
        print("Split Region {} Command executed {}").format(region_id, _sc)
    except:
        print("Split Region {} is faild").format(region_id)

def parse_args():
    parser = argparse.ArgumentParser(description="Show the hot region details and splits")
    parser.add_argument("--th", dest="tidb", help="tidb status url, default: 127.0.0.1:10080", default="127.0.0.1:10080")
    parser.add_argument("--ph", dest="pd", help="pd status url, default: 127.0.0.1:2379", default="127.0.0.1:2379")
    parser.add_argument("database", help="database name")
    parser.add_argument("table",    help="table name")
    args = parser.parse_args()
    return args

if __name__ == "__main__":
    main()