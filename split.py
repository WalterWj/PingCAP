#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import json
import argparse
import shlex
import subprocess

def main():
    args = parse_args()
    _r_regions, _w_regions = region_messges()
    regions = _r_regions + _w_regions
    print("The top Read {} Region is {}").format(args.top, _r_regions)
    print("The top Write {} Region is {}").format(args.top, _w_regions)
    _region = raw_input("Please Enter the region you want to split(Such as ['1','2','3'],default is all):") or ", ".join(regions)
    print(_region)
    try:
        for region_id in _region.split(','):
            print('--{}--').format(region_id)
            if region_id in regions:
                print(region_id)
    except:
        print("Please enter the correct content! Such as ['1','2','3']~")

def Split_region(region_id):
    args = parse_args()
    _split_cmd = "../resources/bin/pd-ctl -u http://{} -d operator add split-region {} --policy=approximate".format(
        args.pd, region_id)
    try:
        _sc = subprocess.check_output(shlex.split(_split_cmd))
        print("Split Region {} Command executed {}").format(region_id, _sc)
    except:
        print("Split Region {} is faild").format(region_id)

def region_messges():
    args = parse_args()
    h_r_region = "../resources/bin/pd-ctl -u http://{} -d region topread {}".format(args.pd, args.top)
    h_w_region = "../resources/bin/pd-ctl -u http://{} -d region topwrite {}".format(args.pd, args.top)
    _r = subprocess.check_output(shlex.split(h_r_region))
    _w = subprocess.check_output(shlex.split(h_w_region))
    r_regions = json.loads(_r)
    w_regions = json.loads(_w)
    _r_regions = _w_regions = []
    print('--------------------TOP 10 Read region messegs--------------------')
    for _r_r in r_regions["regions"]:
        _flow = round(_r_r.get("read_bytes", 0)/1024/1024)
        _db_name, _table_name = table_db_info(_r_r["id"])
        print("leader and region id is [{}] [{}], Store id is {} and IP is {}, and Flow valuation is {}MB," 
            " DB name is {}, table name is {}").format(_r_r["leader"]["id"], _r_r["id"],_r_r["leader"]["store_id"], store_info(_r_r["leader"]["store_id"]), _flow, _db_name, _table_name)
        _r_regions.append(str(_r_r["id"]))

    print('--------------------TOP 10 Write region messegs--------------------')
    for _W_r in w_regions["regions"]:
        _flow = round(_W_r.get("written_bytes", 0)/1024/1024)
        _db_name, _table_name = table_db_info(_r_r["id"])
        print("leader and region id is [{}] [{}], Store id is {} and IP is {}, and Flow valuation is {}MB,"
            " DB name is {}, table name is {}").format(_W_r["leader"]["id"], _W_r["id"], _W_r["leader"]["store_id"], store_info(_W_r["leader"]["store_id"]), _flow, _db_name, _table_name)
        _w_regions.append(str(_W_r["id"]))

    return _r_regions, _w_regions

def table_db_info(region_id):
    args = parse_args()
    httpAPI = "http://{}/regions/{}".format(args.tidb, region_id)
    webContent = subprocess.check_output(["curl", "-sl", httpAPI])
    _table_info = json.loads(webContent)
    if _table_info["frames"] is not None:
        for _info in _table_info["frames"]:
            _db_name = _info.get("db_name", "null")
            _table_name = _info.get("table_name", "null")
    else:
        _db_name = "NUlL"
        _table_name = 'NUll, This table has been drop or truncate'
    return _db_name, _table_name

def store_info(store_id):
    args = parse_args()
    _cmd = "../resources/bin/pd-ctl -u http://{} -d store {}".format(args.pd, store_id)
    _sc = subprocess.check_output(shlex.split(_cmd))
    _store_info = json.loads(_sc)
    info = _store_info["store"]["address"]
    return info

def parse_args():
    parser = argparse.ArgumentParser(description="Show the hot region details and splits")
    parser.add_argument("--th", dest="tidb", help="tidb status url, default: 127.0.0.1:10080", default="127.0.0.1:10080")
    parser.add_argument("--ph", dest="pd", help="pd status url, default: 127.0.0.1:2379", default="172.16.4.51:2379")
    parser.add_argument("--top", dest="top", help="the top read/write region number, default: 10", default="10")
    args = parser.parse_args()
    return args

if __name__ == "__main__":
    main()