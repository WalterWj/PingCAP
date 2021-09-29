#!/bin/bash

settings(){
    # Configuration db information
    db_user='tidb'
    db_port=4000
    # Note: Password cannot be empty ！！！！
    db_password="'tidb@123!@#'"
    db_ip='127.0.0.1'
    # export password
    # MYSQL_PWD=$db_password
}

environment(){
    # Configure MySQL command path
    mysql_path='/usr/local/mysql/bin/mysql'
    ## if dumpling is not exist,then exit
    if [ ! -f $mysql_path ];then
        echo "$mysql_path is not exist~"
        exit 8
    else
        echo "$mysql_path is exist~"
    fi
}

analyze(){
    # Execute analyze table command and run in background
    analyze_table=$($mysql_path -u$db_user -h$db_ip -P$db_port -p$db_password $_dbname -e "analyze TABLE $_table_names;")
}

other(){
    # This place can be adjusted according to demand.
    echo "Can be developed separately"
}

parserDb(){
    # parser db
    local db_sql="select distinct TABLE_SCHEMA from information_schema.tables where TABLE_SCHEMA not in ('METRICS_SCHEMA','PERFORMANCE_SCHEMA','INFORMATION_SCHEMA','mysql') and TABLE_TYPE <> 'VIEW';"
    dbName=$($mysql_path -u $db_user -h $db_ip -P $db_port -p$db_password -e \"$db_sql\")
    echo $dbNmae
    echo "$mysql_path -u $db_user -h $db_ip -P $db_port -p$db_password -e \"$db_sql\""
}

main(){
    # Initialize variables
    settings;
    environment;
    # parser database
    parserDb;
    # local dbName=($dbName)
    # # Get all db names in the library
    # for ((i=1;i<${#dbName[@]};i++)); do
    #     local _dbname=${dbName[i]}
    #     local table_name=$($mysql_path -u$db_user -h$db_ip -P$db_port -p$db_password $_dbname -e "select distinct TABLE_NAME from information_schema.tables where TABLE_SCHEMA ='$_dbname' and TABLE_TYPE <> 'VIEW';")
    #     local table_name=($table_name)
    #     # Get all db names in the library
    #     for ((i=1;i<${#table_name[@]};i++)); do
    #       local _table_names=${table_name[i]}
    #       analyze;
    #       echo "Analyze table $_dbname.$_table_names Sucess~"
    #       sleep 2
    #     done
    # done
}

main;
