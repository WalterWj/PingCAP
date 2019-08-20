# Script specification

## 1. split_hot_region.py
- 脚本说明
  - 主要是为了快速打散读/写热点
  - `TiDB 3.0` 版本开始已经有了打散表的命令，可结合使用。

- 使用说明
  - 需要将整个项目 `git clone` 到 `tidb-ansible/` 目录下，脚本中使用的相对路径调用 `pd-ctl`
  - 可以使用 `split_hot_region.py -h` 获取帮助

- 使用演示
```shell
# 查看脚本说明
[tidb@ip-172-16-4-51 scripts]$ ./split_hot_region.py -h
usage: split.py [-h] [--th TIDB] [--ph PD] top

Show the hot region details and splits

positional arguments:
  top         the top read/write region number

optional arguments:
  -h, --help  show this help message and exit
  --th TIDB   tidb status url, default: 127.0.0.1:10080
  --ph PD     pd status url, default: 127.0.0.1:2379

# 脚本使用
[tidb@ip-172-16-4-51 scripts]$ ./split_hot_region.py --th 127.0.0.1:10080 --ph 172.16.4.51:2379 1
--------------------TOP 1 Read region messegs--------------------
leader and region id is [53] [27], Store id is 7 and IP is 172.16.4.58:20160, and Flow valuation is 11.0MB, DB name is mysql, table name is stats_buckets
--------------------TOP 1 Write region messegs--------------------
leader and region id is [312] [309], Store id is 6 and IP is 172.16.4.54:20160, and Flow valuation is 61.0MB, DB name is mysql, table name is stats_buckets
The top Read 1 Region is 27
The top Write 1 Region is 309
Please Enter the region you want to split(Such as 1,2,3, default is None):27,26
Split Region 27 Command executed 
Please check the Region 26 is in Top
```

**注意:** 在脚本使用过程中，如果不进行内容输入，将会退出脚本。如果想选择性分裂 `region`，请严格按照提醒输入，如：1,2。

## 2. split_table_region.py
- 脚本说明
  - 主要为了分裂小表 `region`
  - `TiDB 3.0` 版本开始已经有了打散表的命令，新版本可以忽略该脚本

- 使用说明
  - 需要将整个项目 `git clone` 到 `tidb-ansible/` 目录下，脚本中使用的相对路径调用 `pd-ctl`
  - 可以使用 `split_table_region.py -h` 获取帮助

- 使用演示
```shell
# 查看帮助
[tidb@ip-172-16-4-51 scripts]$ ./split_table_region.py -h
usage: table_split.py [-h] [--th TIDB] [--ph PD] database table

Show the hot region details and splits

positional arguments:
  database    database name
  table       table name

optional arguments:
  -h, --help  show this help message and exit
  --th TIDB   tidb status url, default: 127.0.0.1:10080
  --ph PD     pd status url, default: 127.0.0.1:2379

# 分裂小表
[tidb@ip-172-16-4-51 scripts]$ ./split_table_region.py --th 127.0.0.1:10080 --ph 172.16.4.51:2379 test t2
Table t2 Info:
  Region id is 26627, leader id is 26628, Store id is 8 and IP is 172.16.4.59:20160

Table t2 Index info:
Index IN_name info, id is 1:
  Region id is 26627 and leader id is 26628, Store id is 8 and IP is 172.16.4.59:20160
Index In_age info, id is 2:
  Region id is 26627 and leader id is 26628, Store id is 8 and IP is 172.16.4.59:20160
We will Split region: ['26627'], y/n(default is yes): y
Split Region 26627 Command executed 
```

## 3. Stats_dump.py

* 脚本目的
  + 快速拿到相关表的统计信息、表结构、版本信息、生成导入统计信息语句
  + 并且内部方便快速导入表结构和统计信息

* 使用说明
  + 该脚本需要访问 `TIDB` 数据库和 `TiDB status url`，需要安装 `pymysql` 包：`sudo pip install pymysql`
  + 可以使用 `Stats_dump.py -h` 获取帮助
  + 最终会生成一个 `tar` 包，解压后，里面有一个 `schema.sql` 文件，里面有 TiDB 的集群信息。
  + 还原统计信息和表结构可以: `mysql -uroot -P4000 -h127.0.0.1 <schema.sql` (注意要在解压缩的目录中执行还原命令)

* 使用演示

```shell
./Stats_dump.py -h
usage: Stats_dump.py [-h] [-tu TIDB] [-H MYSQL] [-u USER] [-p PASSWORD]
                     [-d DATABASE] [-t TABLES]

Export statistics and table structures

optional arguments:
  -h, --help   show this help message and exit
  -tu TIDB     tidb status url, default: 127.0.0.1:10080
  -H MYSQL     Database address and port, default: 127.0.0.1:4000
  -u USER      Database account, default: root
  -p PASSWORD  Database password, default: null
  -d DATABASE  Database name, for example: test,test1, default: None
  -t TABLES    Table name (database.table), for example: test.test,test.test2,
               default: None
```

* 参数说明
  + `-tu` 后填 TIDB 的 IP 地址和 status 端口，端口默认为 10080
  + `-H` 后填 TiDB 的 IP 地址和连接端口，端口默认是 4000
  + `-u` 为数据库登录账户
  + `-p` 为数据库登录密码
  + `-d` 为需要导出统计信息的库，如果使用该参数，就是代表将会导出对应库所有表的统计信息和表结构。比如填 `-d test1,test2`，就是讲 `test1` 和 `test2` 库下的表的统计信息和表结构导出
  + `-t` 导出对应表的统计信息、表结构。需要注意格式：`database_name.table_name`。比如填 `-t test1.t1,test2.t2`，代表将会导出 test1 库 t1 表和 test2 库 t2 表的表结构和统计信息。

* 注意
  + 如果 `-d` 和 `-t` 都没有指定，默认是导出除了系统表以外所有表的统计信息和表结构。
  + 不会导出 `"INFORMATION_SCHEMA", "PERFORMANCE_SCHEMA","mysql", "default"` 库的表结构和统计信息。
  + 该脚本在 `TiDB 3.0` 中执行没有问题，但是由于 2.1 版本不支持 `show create database if not exists db_name;` 语法，如果导出 2.1 版本的 TIDB 统计信息，需要手动修改脚本 [Stats_dump.py](https://github.com/WalterWj/PingCAP/blob/master/Stats_dump.py#L107) 107 行，将 `if not exists` 删除，即可。