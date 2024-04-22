#!/bin/bash

# 全局变量存储配置信息
MASTER_DB=""
MASTER_USER=""
MASTER_PASSWORD=""
SLAVE_DB=""
SLAVE_USER=""
SLAVE_PASSWORD=""
MASTER_PD=""
SLAVE_PD=""
VERSION=""
RELOAD_LIST=""
CHANGEFEED_ID=""
CDC_CONFIG=""
LOCK_USER=""
MOD=""
clusterName=""
SINK_URI=""

# 参数解析函数
parserArgs() {
    while [ "$1" != "" ]; do
        case $1 in
            --masterDB=*)
                MASTER_DB="${1#*=}"
                ;;
            --masterUser=*)
                MASTER_USER="${1#*=}"
                ;;
            --masterPassword=*)
                MASTER_PASSWORD="${1#*=}"
                ;;
            --slaveDB=*)
                SLAVE_DB="${1#*=}"
                ;;
            --slaveUser=*)
                SLAVE_USER="${1#*=}"
                ;;
            --slavePassword=*)
                SLAVE_PASSWORD="${1#*=}"
                ;;
            --masterPD=*)
                MASTER_PD="${1#*=}"
                ;;
            --slavePD=*)
                SLAVE_PD="${1#*=}"
                ;;
            --version=*)
                VERSION="${1#*=}"
                ;;
            --reloadList=*)
                RELOAD_LIST="${1#*=}"
                ;;
            --changefeedID=*)
                CHANGEFEED_ID="${1#*=}"
                ;;
            --cdcConfig=*)
                CDC_CONFIG="${1#*=}"
                ;;
            --lockUser=*)
                LOCK_USER="${1#*=}"
                ;;
            --mod=*)
                MOD="${1#*=}"
                ;;
            --clusterName=*)
                clusterName="${1#*=}"
                ;;
            --sink-uri=*)
                SINK_URI="${1#*=}"
                ;;
            *)
                echo "无效参数：$1"
                usage
                exit 1
                ;;
        esac
        shift
    done

    # 检查是否所有必需的参数都已设置
    if [ -z "$MASTER_DB" ] || [ -z "$MASTER_USER" ] || [ -z "$MASTER_PASSWORD" ] ||
       [ -z "$SLAVE_DB" ] || [ -z "$SLAVE_USER" ] || [ -z "$SLAVE_PASSWORD" ] ||
       [ -z "$MASTER_PD" ] || [ -z "$SLAVE_PD" ] || [ -z "$VERSION" ] || [ -z "$RELOAD_LIST" ] ||
       [ -z "$CHANGEFEED_ID" ] || [ -z "$CDC_CONFIG" ] || [ -z "$LOCK_USER" ] ||
       [ -z "$MOD" ] || [ -z "$clusterName" ] || [ -z "$SINK_URI" ]; then
        echo "缺少必需的参数。"
        usage
        exit 1
    fi
}

# 使用说明函数
usage() {
    echo "使用方法: $0 --clusterName=<集群名称> --masterDB=<数据库主机:端口> --masterUser=<用户名> --masterPassword=<密码> --slaveDB=<数据库从机:端口> --slaveUser=<用户名> --slavePassword=<密码> --masterPD=<PD主机:端口> --slavePD=<PD从机:端口> --version=<版本> --reloadList=<主机列表> --changefeedID=<changefeed标识> --cdcConfig=<配置文件> --lockUser=<锁定用户列表> --mod=<执行模式> --sink-uri=<TiDB连接URI>"
    # 逻辑代码
    echo "主库数据库: $MASTER_DB"
    echo "主库用户: $MASTER_USER"
    echo "主库密码: $MASTER_PASSWORD"
    echo "Master PD 服务: $MASTER_PD"
    echo "从库数据库: $SLAVE_DB"
    echo "从库用户: $SLAVE_USER"
    echo "从库密码: $SLAVE_PASSWORD"
    echo "Slave PD 服务: $SLAVE_PD"
    echo "CDC 版本: $VERSION"
    echo "重载列表: $RELOAD_LIST"
    echo "Changefeed 标识: $CHANGEFEED_ID"
    echo "CDC 配置文件: $CDC_CONFIG"
    echo "锁定用户: $LOCK_USER"
    echo "新建 cdc 同步 uri: $SINK_URI"
    echo "执行模式: $MOD,
    1. 用户锁定
    2. 重启 tidb server 节点
    3. 确认是否有留存连接
    4. 等待 cdc 任务同步追上
    5. 删除 master cdc 任务
    6. 创建从库到主库的同步
    7. 解锁从库应用用户"
}

# 锁定账户
userLock() {
    # 获取用户
    local userAccounts=$LOCK_USER
    # 读取账户到数组
    IFS=',' read -ra ACCOUNTS <<< "$userAccounts"
    # 创建一个新的数组用于存储过滤后的账户
    filtered_accounts=()

    # 遍历 ACCOUNTS 数组
    for account in "${ACCOUNTS[@]}"; do
        # 过滤掉包含 root@'%'
        if [[ "$account" != "root@'%'" ]]; then
            filtered_accounts+=("$account")
        fi
    done

    # 锁定操作开始
    for account in "${filtered_accounts[@]}"; do
        echo "Locking account: $account"
        IFS=':' read -r ip port <<< "$MASTER_DB"
        mysql -h "$ip" -u "$MASTER_USER" -p"$MASTER_PASSWORD" -P "$port" -e "ALTER USER $account ACCOUNT LOCK;FLUSH PRIVILEGES;"
        if [ $? -eq 0 ]; then
            echo "Successfully locked: $account"
        else
            echo "Failed to lock: $account"
            exit 1
        fi
    done
}

# 重启 tidb-server 节点
restartTidb(){
    local tidbList=$RELOAD_LIST
    # 使用数组来安全地存储和执行命令
    local command=(~/.tiup/bin/tiup cluster reload "$clusterName" -R tidb -N "$tidbList" -c 200 -y)

    # 使用echo显示命令
    echo "执行重启命令：${command[*]}"

    # 执行命令
    "${command[@]}"

    # 检查命令执行的返回值
    if [ $? -eq 0 ]; then
        echo "Reload command executed successfully."
    else
        echo "Reload command failed."
        exit 1
    fi
}

# 确定是否有相关账户连接留存
checkConnect(){
    # master 的 ip 端口
    IFS=':' read -r ip port <<< "$MASTER_DB"
    #  封的用户：kfc_login@'%',phhs_login@'%' 转为：'kfc_login','phhs_login'
    local users=$(echo $LOCK_USER|sed "s/@'%'//g" | sed "s/,/','/g")
    # count 行数
    local command=(mysql -h "$ip" -u "$MASTER_USER" -p"$MASTER_PASSWORD" -P "$port" -e \
    "select count(1) as count from information_schema.cluster_processlist where USER in ('','$users');")
    # 输出命令
    echo "查看连接 SQL："
    echo ${command[*]}
    # 执行命令
    local result
    result=$("${command[@]}")
    local status=$?  # 保存 mysql 命令的退出状态
    # 检查命令执行的返回值
    if [ $status -eq 0 ]; then
        echo "count command executed successfully."
    else
        echo "count command failed."
        exit 1
    fi
    # 行数判断
    echo "'$users' 账户的连接数为:" $result
    # 去除结果 \n
    local result=$(echo $result | tr -d '\n')
    if [ "$result" = "count 0" ]; then
        echo "无连接，继续脚本"
    else
        echo "尚存连接，即将退出"
        exit 1
fi
}

# 获取 cdc tso
getCheckPoint(){
    # 执行查询命令
    local command=(~/.tiup/bin/tiup cdc:$VERSION cli changefeed query -s --pd=http://$MASTER_PD --changefeed-id=$CHANGEFEED_ID)
    # 输出命令
    echo "取 cdc 获取同步任务状态命令: "
    echo ${command[*]}
    # 执行命令
    local result
    result=$("${command[@]}")
    ## 这里是测试问题看结果
    #local result
    #local result=$(cat ./tmp.txt)
    # 检查命令执行的返回值
    if [ $? -eq 0 ]; then
        echo "get CDC checkpoint tso command executed successfully."
    else
        echo "get CDC checkpoint tso command failed."
        exit 1
    fi
    # 获取 tso
    cdcCheckPoint=$(echo "$result" | tr '\r' '\n' | grep "checkpoint_tso" | sed -n 's/.*"checkpoint_tso": \([0-9]*\),.*/\1/p')
    echo "CDC check Point TSO: $cdcCheckPoint"
    echo "$cdcCheckPoint"
}

# 确定 cdc 任务
checkCdcStatus(){
    # master 的 ip 端口
    IFS=':' read -r ip port <<< "$MASTER_DB"
    # 获取 master 当前 TSO
    local masterCommand=(mysql -h "$ip" -u "$MASTER_USER" -p"$MASTER_PASSWORD" -P "$port" -e
    "show master status;")
    # 输出命令
    echo ${masterCommand[*]}
    # 执行命令
    local masterResult
    masterResult=$("${masterCommand[@]}")
    local status=$?
    # 检查命令执行的返回值
    if [ $status -eq 0 ]; then
        echo "get Master tso command executed successfully."
    else
        echo "get Master tso command failed."
        exit 1
    fi
    # 结果格式化，取第二行最后一个字段内容，也就是 pos 值
    local masterPos=$(echo "$masterResult" | awk 'NR==2 {print $NF}')
    echo "master pos 为：$masterPos"

    # 定义循环控制变量
    ctlNum=5
    ctmTmp=1
    # 进入循环
    while [ $ctmTmp -le $ctlNum ]; do
        echo "循环 $ctmTmp 次"
        # 等待一小段时间，获取 cdc 同步位点
        waitTime=3
        echo "等待 $waitTime s"
        sleep $waitTime;

        # 获取 checkpoint，获取 func 最后一个 echo
        local checkPoint=$(getCheckPoint | tail -n 1)
        # echo $checkPoint
        if [[ "$checkPoint" =~ ^-?[0-9]+$ ]]; then
            echo "Checkpoint: $checkPoint is a integer number."
        else
            echo "Checkpoint: $checkPoint is not a integer number. exit!!"
            exit 1
        fi
        # 比较 checkpoint 和 master tso，如果 checkpoint 大于等于 master tso
        if [[ $checkPoint -ge $masterPos ]]; then
            echo "checkPoint ($checkPoint) is greater than or equal to masterPos ($masterPos). Breaking the loop."
            break  # 如果 checkPoint 大于等于 masterPos，跳出循环
        else
            echo "checkPoint ($checkPoint) is less than masterPos ($masterPos). Continuing the loop."
        fi
        # 增加迭代器
        ctmTmp=$(( ctmTmp + 1 ))
    done
    # 添加如果循环判断到最后，同步都没有追上，退出脚本
    if [[ $ctmTmp -le $ctlNum ]]; then
        # 判断结束
        echo "判断结束"
    else
        echo "超过判断次数，退出整个脚本"
        exit 1;
    fi
}

# master cdc 任务删除
deleteCdcTask(){
    # 暂停任务
    pauseTaskCommand=(~/.tiup/bin/tiup cdc:$VERSION cli changefeed pause --pd=http://$MASTER_PD --changefeed-id=$CHANGEFEED_ID)
    # 输出命令
    echo "暂停 cdc 同步任务命令: "
    echo ${pauseTaskCommand[*]}
    # 执行命令
    "${pauseTaskCommand[@]}"
    # 检查命令执行的返回值
    if [ $? -eq 0 ]; then
        echo "Pause CDC task command executed successfully."
    else
        echo "Pause CDC task command failed."
        exit 1
    fi
    # 删除任务
    removeTaskCommand=(~/.tiup/bin/tiup cdc:$VERSION cli changefeed remove --pd=http://$MASTER_PD --changefeed-id=$CHANGEFEED_ID)
    # 输出命令
    echo "暂停 cdc 同步任务命令: "
    echo ${removeTaskCommand[*]}
    # 执行命令
    "${removeTaskCommand[@]}"
    # 检查命令执行的返回值
    if [ $? -eq 0 ]; then
        echo "Remove CDC task command executed successfully."
    else
        echo "Remove CDC task command failed."
        exit 1
    fi
}

createCdcTask(){
    # slave 的 ip 端口
    IFS=':' read -r ip port <<< "$SLAVE_DB"
    # 获取 slave 当前 TSO
    local slaveCommand=(mysql -h "$ip" -u "$SLAVE_USER" -p"$SLAVE_PASSWORD" -P "$port" -e
    "show master status;")
    # 输出命令
    echo ${slaveCommand[*]}
    # 执行命令
    local slaveResult
    slaveResult=$("${slaveCommand[@]}")
    local status=$?
    # 检查命令执行的返回值
    if [ $status -eq 0 ]; then
        echo "get Slave tso command executed successfully."
    else
        echo "get Slave tso command failed."
        exit 1
    fi
    # 结果格式化，取第二行最后一个字段内容，也就是 pos 值
    local slavePos=$(echo "$slaveResult" | awk 'NR==2 {print $NF}')
    echo "slave 的 pos 为：$slavePos"

    # 从库创建任务
    createTaskCommand=(~/.tiup/bin/tiup cdc:$VERSION cli changefeed create --pd=http://$SLAVE_PD \
    --changefeed-id=$CHANGEFEED_ID --sink-uri="$SINK_URI" --config=$CDC_CONFIG --start-ts="$slavePos")
    # 输出命令
    echo "创建 cdc 同步任务命令: "
    echo ${createTaskCommand[*]}
    # 执行命令
    "${createTaskCommand[@]}"
    # 检查命令执行的返回值
    if [ $? -eq 0 ]; then
        echo "Create CDC task command executed successfully."
    else
        echo "Create CDC task command failed."
        exit 1
    fi
}

# 解锁从库 user
userUnLock() {
    local userAccounts=$LOCK_USER
    # 解析数据库用户名
    IFS=',' read -ra ACCOUNTS <<< "$userAccounts"
    for account in "${ACCOUNTS[@]}"; do
        echo "UnLock account: $account"
        # 解析数据库账号密码
        IFS=':' read -r ip port <<< "$SLAVE_DB"
        mysql -h "$ip" -u "$SLAVE_USER" -p"$SLAVE_PASSWORD" -P "$port" -e "ALTER USER $account ACCOUNT UNLOCK;FLUSH PRIVILEGES;"
        if [ $? -eq 0 ]; then
            echo "Successfully Unlocked: $account"
        else
            echo "Failed to Unlock: $account"
            exit 1
        fi
    done
}

# 主逻辑函数
main() {
    parserArgs "$@"
    # 逻辑代码
    echo "主库数据库: $MASTER_DB"
    echo "主库用户: $MASTER_USER"
    echo "主库密码: $MASTER_PASSWORD"
    echo "Master PD 服务: $MASTER_PD"
    echo "从库数据库: $SLAVE_DB"
    echo "从库用户: $SLAVE_USER"
    echo "从库密码: $SLAVE_PASSWORD"
    echo "Slave PD 服务: $SLAVE_PD"
    echo "CDC 版本: $VERSION"
    echo "重载列表: $RELOAD_LIST"
    echo "Changefeed 标识: $CHANGEFEED_ID"
    echo "CDC 配置文件: $CDC_CONFIG"
    echo "锁定用户: $LOCK_USER"
    echo "新建 cdc 同步 uri: $SINK_URI"
    echo "执行模式: $MOD,
    1. 用户锁定
    2. 重启 tidb server 节点
    3. 确认是否有留存连接
    4. 等待 cdc 任务同步追上
    5. 删除 master cdc 任务
    6. 创建从库到主库的同步
    7. 解锁从库应用用户"
    # 开始任务
    echo "<-------->开始任务<-------->"
    # 1. 用户锁定
    # userLock;
    # 2. 重启 tidb server 节点
    # restartTidb;
    # 3. 确认是否有留存连接
    # checkConnect;
    # 4. 等待 cdc 任务同步追上
    # checkCdcStatus;
    # 5. 删除 master cdc 任务
    # deleteCdcTask;
    # 6. 创建从库到主库的同步
    # createCdcTask;
    # 7. 解锁从库应用用户
    # userUnLock;
    # 根据 mod 模式来执行步骤
    # 根据传入的模式执行对应的函数
    # 根据传入的模式执行对应的函数
    IFS=',' read -ra ADDR <<< "$MOD"
    for i in "${ADDR[@]}"; do
        case $i in
            1)
                echo "Step 1: 用户锁定"
                userLock
                ;;
            2)
                echo "Step 2: 重启 TiDB server 节点"
                restartTidb
                ;;
            3)
                echo "Step 3: 确认是否有留存连接"
                checkConnect
                ;;
            4)
                echo "Step 4: 等待 CDC 任务同步追上"
                checkCdcStatus
                ;;
            5)
                echo "Step 5: 删除 master CDC 任务"
                deleteCdcTask
                ;;
            6)
                echo "Step 6: 创建从库到主库的同步"
                createCdcTask
                ;;
            7)
                echo "Step 7: 解锁从库应用用户"
                userUnLock
                ;;
            *)
                echo "无效的选项: $i"
                ;;
        esac
    done
}

# 脚本入口点
if [ "${BASH_SOURCE[0]}" -ef "$0" ]; then
    main "$@"
fi

# 测试命令
# ./failoverByCDC.sh --masterDB='10.1xxx02.58.180:4000' --masterUser='root' --masterPassword='tidbxx' --masterPD='10.xxx:2379' --slaveDB='10.102.5xx:4000' --slaveUser='root' --slavePassword='tidb@123' --slavePD='10.1xxx1:2379' --version='v7.1.4' --reloadList='172.xxx:4000,172.xxx.47:4000' --changefeedID='usexbackup' --cdcConfig='cdc.conf' --lockUser="xin@'%',px@'%',tidb@'%'" --mod='1,2,3' --clusterName="tidb-test" --sink-uri="tidb://root:w@-xxxxxxR@172.20.xx:4000/&transaction-atomicity=none"
