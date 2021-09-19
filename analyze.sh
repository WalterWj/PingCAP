#!/bin/bash

settings(){
    # Configuration db information
    # db_name='test'
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
    analyze_table=$(($mysql_path -u$db_user -h$db_ip -P$db_port -p$db_password $d_name -e "analyze TABLE $1;") >> analyze.log &)
}

other(){
    # This place can be adjusted according to demand.
    echo "Can be developed separately"
}

main(){
    # Initialize variables
    settings;
    environment;
    
    # Get all databases in the instance
    local db_name=$($mysql_path -u$db_user -h$db_ip -P$db_port -p$db_password $db_name -e "show databases;")
    local db_name=($db_name)

    echo '==================begin==================' >> analyze.log
    current_time=`date +"%Y-%m-%d %H:%M:%S"`
    echo $current_time >> analyze.log

    # Loop analyze all tables of each database    
    for ((i=1;i<${#db_name[@]};i++))
    do
      local d_name=${db_name[i]}
      if  [ "$d_name" != "test" ] && [ "$d_name" != "mysql" ] && [ "$d_name" != "INFORMATION_SCHEMA" ] && [ "$d_name" != "METRICS_SCHEMA" ] && [ "$d_name" != "PERFORMANCE_SCHEMA" ];then
        echo "----use database: $d_name----" >> analyze.log

        local table_name=$($mysql_path -u$db_user -h$db_ip -P$db_port -p$db_password $d_name -e "show tables;")
        local table_name=($table_name)
        for ((j=1;j<${#table_name[@]};j++))
        do
          local table_names=${table_name[j]}
          echo "analyze table：$table_names" >> analyze.log
          analyze $table_names;
          # other;
          sleep 0.5
        done
      fi
      # other;
      #sleep 0.5
    done
    echo '==================end==================' >> analyze.log
}

main;
