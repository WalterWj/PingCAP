#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import json
import argparse
import shlex
import subprocess

def main():
    pass



def parse_args():
    parser = argparse.ArgumentParser(
        description="Show the hot region details and splits")
    parser.add_argument("--th",
                        dest="tidb",
                        help="tidb status url, default: 127.0.0.1:10080",
                        default="127.0.0.1:10080")
    parser.add_argument("--ph",
                        dest="pd",
                        help="pd status url, default: 127.0.0.1:2379",
                        default="127.0.0.1:2379")
    parser.add_argument("top", help="the top read/write region number")
    args = parser.parse_args()
    return args


if __name__ == "__main__":
    main()
