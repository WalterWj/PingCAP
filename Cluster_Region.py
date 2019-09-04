#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import json
import argparse
import shlex
import subprocess


def main():
    parsers = {}
    args = parse_args()
    regions = parser_regions(args.pd)
    parsers["total"] = regions["count"]
    for region in regions["regions"]:
        if region.get("approximate_size", None) is None or region.get(
            "approximate_keys", None) is None:
            parsers["empty"] = 1 + parsers.get("empty", 0)
        elif region["approximate_size"] <= int(
            args.size) and region["approximate_keys"] <= int(args.keys):
            parsers["conform"] = 1 + parsers.get("conform", 0)
        elif region["approximate_size"] <= int(
            args.size) and region["approximate_keys"] > int(args.keys):
            parsers["incompatible-keys"] = 1 + parsers.get("incompatible-keys",
                                                           0)
        elif region["approximate_size"] > int(
            args.size) and region["approximate_keys"] <= int(args.keys):
            parsers["incompatible-size"] = 1 + parsers.get("incompatible-size",
                                                           0)
        elif region["approximate_size"] > int(
            args.size) and region["approximate_keys"] > int(args.keys):
            parsers["incompatible"] = 1 + parsers.get("incompatible", 0)
        else:
            parsers["errors"] = 1 + parsers.get("error", 0)

    print(
        "Total: {} \nNumber of empty regions: {} \nThe regions that can be merged: {} \nJust does not meet the limit of key: {} \nJust not meeting the size limit: {} \nDoes not meet all restrictions: {} \nParser errors: {}".format(
            parsers["total"], parsers.get("empty", 0),
            parsers.get("conform", 0), parsers.get("incompatible-keys", 0),
            parsers.get("incompatible-size", 0),
            parsers.get("incompatible", 0), parsers.get("error", 0)))


def parser_regions(pd_Api):
    regions_cmd = "../resources/bin/pd-ctl -u http://{} -d region".format(pd_Api)
    regions = subprocess.check_output(shlex.split(regions_cmd))
    regions = json.loads(regions)

    return regions


def parse_args():
    parser = argparse.ArgumentParser(
        description="Show the hot region details and splits")
    parser.add_argument("-pd",
                        dest="pd",
                        help="pd status url, default: 127.0.0.1:2379",
                        default="127.0.0.1:2379")
    parser.add_argument("-s",
                        dest="size",
                        help="Region size(MB), default: 20",
                        default="20")
    parser.add_argument("-k",
                        dest="keys",
                        help="Region keys, default: 200000",
                        default="200000")
    args = parser.parse_args()

    return args


if __name__ == "__main__":
    main()
