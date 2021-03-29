#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import argparse
import pymysql
import json

# If Python is version 2.7, encoding problems can reload sys configuration
try:
    import sys

    reload(sys)
    sys.setdefaultencoding('utf-8')
except:
    pass


def main():
    args = parse_args()
    ack = "no"
    ct = 0
    while ack == "no":
        ct += 1
        ack = mysql_execute()
        print("Connection retries {}".format(ct))
        if ct >= 100:
            ack = "yes"

def mysql_execute():
    # Connect to MySQL and execute SQL commands
    args = parse_args()
    config = {
        "host": args.mysql,
        "port": int(args.port),
        "user": args.user,
        "password": args.password,
        "charset": 'utf8mb4',
        # "cursorclass": pymysql.cursors.DictCursor
    }

    connection = pymysql.connect(**config)
    cursor = connection.cursor()
    _sql = "select @@tidb_config;"
    try:
        cursor.execute(_sql)
        content = cursor.fetchall()
        connection.commit()
    except:
        print(
            "SQL {} execution failed~"
            .format(_sql))
    finally:
        print(args.advertiseAddress, args.advertisePort)
        config_c = json.loads(content[0][0])
        if config_c["advertise-address"].strip() == args.advertiseAddress and str(config_c["port"]).strip() == args.advertisePort:
            print("The TiDB IP is {}".format(config_c["advertise-address"]))
            print("The TiDB IP Port is {}".format(config_c["port"]))
            sql_kill = "kill tidb {}".format(args.sessionId)
            _ct = str(input("Will execute: {}, y/n (default:yes)".format(sql_kill))) or "y"
            if _ct == "y":
                cursor.execute(sql_kill)
            else:
                print("SQL {} cancel execution".format(sql_kill))
            ack = "yes"
            cursor.close()
            connection.close()
        else:
            cursor.close()
            connection.close()
            ack = "no"

    return ack


def parse_args():
    # Incoming parameters
    parser = argparse.ArgumentParser(
        description="Kill TiDB session by id")
    parser.add_argument("-P",
                        dest="port",
                        help="tidb port, default: 4000",
                        default=4000)
    parser.add_argument("-H",
                        dest="mysql",
                        help="Database address, default: 127.0.0.1",
                        default="127.0.0.1")
    parser.add_argument("-u",
                        dest="user",
                        help="Database account, default: root",
                        default="root")
    parser.add_argument("-p",
                        dest="password",
                        help="Database password, default: null",
                        default="")
    parser.add_argument("-a",
                        dest="advertiseAddress",
                        help="TiDB Address, default: null",
                        default="")
    parser.add_argument("-ap",
                        dest="advertisePort",
                        help="TiDB Port, default: 4000",
                        default="4000")
    parser.add_argument("-id",
                        dest="sessionId",
                        help="session id, default: null",
                        default="")
    args = parser.parse_args()

    return args


if __name__ == "__main__":
    main()
