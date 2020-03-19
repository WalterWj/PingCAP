#!/bin/bash

settings(){
    # Configuration db information
    db_name='test'
    db_user='root'
    db_port=4000
    # Note: Password cannot be empty ！！！！
    db_password="123"
    db_ip='127.0.0.1'
}

environment(){
    # Configure MySQL command path
    mysql_path='/usr/local/bin/mysql'
}

analyze(){
    # Execute analyze table command and run in background
    analyze_table=$(($mysql_path -u$db_user -h$db_ip -P$db_port -p$db_password $db_name -e "analyze TABLE $table_names;") >> analyze.log &)
}

other(){
    # This place can be adjusted according to demand.
    echo "Can be developed separately"
}

main(){
    # Get all table names in the library
    local table_name=$($mysql_path -u$db_user -h$db_ip -P$db_port -p$db_password $db_name -e "show tables;")
    local table_name=($table_name)

    # Loop analyze all tables
    for ((i=1;i<${#table_name[@]};i++))
    do
      local table_names=${table_name[i]}
      echo "Analyze table "$table_names
      analyze;
      # other;
      sleep 0.5
    done
}

settings;
environment;
main;
