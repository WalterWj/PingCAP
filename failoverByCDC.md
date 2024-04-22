# 使用说明
这个脚本是一个用于管理 TiDB 集群和 CDC 同步任务的 Bash 脚本。它包含多项功能，例如数据库用户锁定、重启 TiDB 服务器节点、检查连接、管理 CDC 任务等。以下是该脚本的详细使用说明：

## 脚本功能
该脚本主要用于TiDB数据库的主从切换及数据同步任务的管理。它可以执行以下操作：

1. 锁定指定的数据库用户
2. 重启 TiDB 服务节点
3. 检查是否有连接留存
4. 等待 CDC 同步任务赶上当前数据状态
5. 删除现有的 CDC 同步任务
6. 在从库创建新的 CDC 同步任务
7. 解锁数据库用户

## 使用方法
脚本通过命令行参数接收配置信息，并根据这些参数执行不同的操作。使用示例如下：

```shell
./failoverByCDC.sh [参数列表]
```

## 参数列表
脚本支持以下参数：
- --clusterName=<集群名称>: 指定操作的 TiDB 集群名称。
- --masterDB=<主数据库地址:端口>: 主数据库的地址和端口，格式为 IP:端口。
- --masterUser=<主数据库用户名>: 用于访问主数据库的用户名。
- --masterPassword=<主数据库密码>: 用于访问主数据库的密码。
- --slaveDB=<从数据库地址:端口>: 从数据库的地址和端口，格式同主数据库。
- --slaveUser=<从数据库用户名>: 用于访问从数据库的用户名。
- --slavePassword=<从数据库密码>: 用于访问从数据库的密码。
- --masterPD=<PD主服务地址:端口>: 主 PD (Placement Driver) 服务的地址和端口，PD 是 TiDB 集群的元数据管理组件。
- --slavePD=<PD从服务地址:端口>: 从 PD 服务的地址和端口。
- --version=<CDC版本>: 指定 TiCDC 的版本，TiCDC 是 TiDB 集群的变更数据捕获组件。
- --reloadList=<重启节点列表>: 需要重启的 TiDB 节点的地址和端口列表，多个地址用逗号分隔。
- --changefeedID=<changefeed标识>: CDC 同步任务的唯一标识。
- --cdcConfig=<CDC配置文件路径>: CDC 同步任务的配置文件路径。
- --lockUser=<锁定的用户列表>: 需要锁定的数据库用户列表，多个用户用逗号分隔，格式为 用户名@'主机'。
- --mod=<执行模式>: 指定脚本执行的具体步骤，用逗号分隔的数字序列表示，每个数字对应脚本中定义的一个操作步骤。
- --sink-uri=<新 CDC 同步的 TiDB 连接 URI>: 新的 CDC 同步任务的目标 TiDB 实例的连接 URI。

## 示例
以下是一个使用示例：

```shell
./failoverByCDC.sh --clusterName="tidb-test" \
--masterDB='10.xxx:4000' \
--masterUser='root' \
--masterPassword='tidbxxx' \
--masterPD='10.xxx:2379' \
--slaveDB='10.xxx:4000' \
--slaveUser='root' \
--slavePassword='tidb@123' \
--slavePD='10.102.173.121:2379' \
--version='v7.1.4' \
--reloadList='172.xxx:4000,172xxx:4000' \
--changefeedID='userxxkup' \
--cdcConfig='cdc.conf' \
--lockUser="xin@'%',pxlogin@'%',tidb@'%'" \
--mod='1,2,3' \
--sink-uri="tidb://root:w@-xxx@1xx.xxx:4000/&transaction-atomicity=none"
```

## 示例参数解释
- --mod='1,2,3'：这个参数决定了脚本中执行的操作序列。每个数字对应脚本中定义的一个操作步骤。例如，在上面的示例中，1,2,3 分别表示：
  - 1 - 锁定用户
  - 2 - 重启 TiDB server 节点
  - 3 - 检查是否有留存连接
mod 参数的可选值及其对应功能
- 1 锁定用户
- 2 重启 TiDB server 节点
- 3 检查是否有留存连接
- 4 等待 CDC 任务同步追上
- 5 删除 master CDC 任务
- 6 创建从库到主库的同步
- 7 解锁从库应用用户
您可以根据需要任意组合这些数字来指定执行的步骤。例如，如果只想删除 CDC 任务并创建新的同步任务，可以设置 --mod='5,6'。

## 注意事项
- 确保所有涉及的数据库、用户及其他配置信息都是正确的。
- 用逗号分隔 --mod 参数中的数字，不要有空格。
- 确保脚本和相关命令行工具具有执行权限，并在可以访问 TiDB 和 CDC 的环境中执行。
- 确保脚本具有执行权限，可使用 chmod +x failoverByCDC.sh 命令来设置。
- 该脚本需要在具有访问数据库和执行 TiDB、CDC 命令的环境中运行。
- 传入的参数应根据实际环境进行调整。

通过适当配置这些参数，灵活地使用此脚本来管理 TiDB 集群和 CDC 任务。
