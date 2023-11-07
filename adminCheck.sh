#!/bin/bash

settings() {
    # Configuration db information
    db_user='root'
    db_port=4100
    # Note: Password cannot be empty ！！！！
    db_password="root"
    db_ip='127.0.0.1'
    db_name='test test1 test2'
    variable='tidb_distsql_scan_concurrency=30'
}

environment() {
    # Configure MySQL command path
    mysql_path='/usr/bin/mysql'
    ## if MySQL is not exist,then exit
    if [ ! -f $mysql_path ]; then
        echo "$mysql_path is not exist~"
        exit 8
    else
        echo "$mysql_path is exist~"
    fi
}

getTso() {
    # Get TSO
    tso=`$mysql_path -u $db_user -p$db_password -h $db_ip -P $db_port -e "show master status;"`
    # echo "$tso" | grep binlog | awk -F' ' '{{print $2}}'
}

main() {
    settings;
    environment;
    getTso;
    local tso=`echo "$tso" | grep binlog | awk -F' ' '{{print $2}}'`

    # Get tables
    for dbsName in $db_name; do
        local sql="SELECT
            table_schema AS DatabaseName,
            table_name AS TableName,
            index_name AS IndexName,
            GROUP_CONCAT(column_name ORDER BY seq_in_index ASC) AS Columns
            FROM information_schema.statistics
            WHERE table_schema = '$dbsName'
        GROUP BY table_schema, table_name, index_name
        ORDER BY table_schema, table_name, index_name;
        "
        tables=$($mysql_path -u$db_user -p$db_password -h $db_ip -P $db_port -e "$sql")
        echo "$tables" | awk -F' ' '{{print $2,$3,$4}}' | grep -Ev 'TableName' >info.tables
        while read -r line; do
            # 使用适当的方法来提取信息，假设以空格分隔
            table_name=$(echo $line | cut -d ' ' -f 1)
            index_type=$(echo $line | cut -d ' ' -f 2)

            # 使用循环来处理剩余的信息
            for column in $(echo $line | cut -d ' ' -f 3-); do
                echo "Database: $dbsName,Table: $table_name, Index Type: $index_type, Column: $column"
                # 在这里可以执行任何需要的操作
                local indexInfo=$column
                local database=$dbsName
                local table=$table_name
                local tso=$tso
                local othersql="set tidb_snapshot=$tso;set $variable"
                local current_datetime=$(date +"%Y-%m-%d %H:%M:%S")
                if [ $index_type = "PRIMARY" ];then
                    echo "$current_datetime 主键跳过";
                    # XoRSQL="select (bit_xor(concat($indexInfo))) as bitXor from $database.$table use index(primary);"
                else
                    local XoRSQL="select (bit_xor(concat($indexInfo))) as bitXor from $database.$table ;"
                    # Get XOR Bit
                    # echo $XoRSQL
                    local xor_bit=$($mysql_path -u $db_user -p$db_password -h $db_ip -P $db_port -e "$othersql;$XoRSQL")
                    local xor=`echo $xor_bit|awk -F' ' '{{print $2}}'`
                    local XoRSQLPrimary="select (bit_xor(concat($indexInfo))) as bitXor from $database.$table use index(primary);"
                    local xor_bit=$($mysql_path -u $db_user -p$db_password -h $db_ip -P $db_port -e "$othersql;$XoRSQL")
                    local xorPrimary=`echo $xor_bit|awk -F' ' '{{print $2}}'`
                    if [ $xor != $xorPrimary ];then
                        echo "$current_datetime xor: $xor,xorPrimary: $xorPrimary, 校验不通过"
                    else
                        echo "$current_datetime xor: $xor,xorPrimary: $xorPrimary, 校验通过"
                    fi
                fi

            done
        done <info.tables
    done
}

# settings;
# environment;
# getTso;
main;

