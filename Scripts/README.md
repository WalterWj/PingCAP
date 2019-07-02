# Script specification

## 1. split_hot_region.py
- 脚本说明
  - 主要是为了快速打散热点
  - TiDB 3.0 版本开始已经有了打散表的命令，可结合使用。

- 使用说明
  - 需要将脚本放在 tidb-ansible/scripts 目录下
  - 可以使用 split_hot_region.py -h 获取帮助

- 使用演示
```shell
# 查看脚本说明
[tidb@ip-172-16-4-51 scripts]$ ./split.py -h
usage: split.py [-h] [--th TIDB] [--ph PD] top

Show the hot region details and splits

positional arguments:
  top         the top read/write region number

optional arguments:
  -h, --help  show this help message and exit
  --th TIDB   tidb status url, default: 127.0.0.1:10080
  --ph PD     pd status url, default: 127.0.0.1:2379

# 脚本使用
[tidb@ip-172-16-4-51 scripts]$ ./split.py --th 127.0.0.1:10080 --ph 172.16.4.51:2379 top 1
--------------------TOP 10 Read region messegs--------------------
leader and region id is [53] [27], Store id is 7 and IP is 172.16.4.58:20160, and Flow valuation is 11.0MB, DB name is mysql, table name is stats_buckets
--------------------TOP 10 Write region messegs--------------------
leader and region id is [312] [309], Store id is 6 and IP is 172.16.4.54:20160, and Flow valuation is 61.0MB, DB name is mysql, table name is stats_buckets
The top Read 1 Region is 27
The top Write 1 Region is 309
Please Enter the region you want to split(Such as 1,2,3, default is all):27,26
Split Region 27 Command executed 
Please check the Region 26 is in Top
```

**注意:** 在脚本使用过程中，如果不进行内容输入，将会分裂所有 TOP 读写热点 region。如果想选择性分裂 region，请严格按照提醒输入，如：1,2。