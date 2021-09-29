#!/bin/bash

init(){
# database info
user='tidb'
port=4000
password='tidb@123!@#'
filetype='sql'
thread=4
host='127.0.0.1'

# backup 
_time=$(date '+%Y%m%d')
backupDir='/tidbbackup/fmtfx_back/'
# dir
backupDir+=$_time

# Old
oldTime=$(date -d '2 day ago' '+%Y%m%d')
oldDir='/tidbbackup/fmtfx_back/'
# dir
oldDir+=$oldTime

# other
## log
logFile='/tidbbackup/fmtfx_back/main.log'
## log time
logTime=$(date '+%Y/%m/%d %H:%M:%S')
## binary dir
binaryPath='/home/db/tidbmgt/tools'
_dir='/tidbbackup/fmtfx_back/'
}

mkDir(){
if [ ! -d $_dir  ];then
    mkdir -p $_dir
else
    echo "$_dir exist~"
fi
}

rmBackup(){
    # rm -rf Previous backup
    rm -rf $oldDir && echo "[$logTime] Delete $oldDir Sucess~" &>> 'execute.log'
}

dump(){
# cd base path
cd $binaryPath;
nohup ./dumpling \
  -u $user \
  -P $port \
  -p $password \
  -h $host \
  --filetype $filetype \
  -t $thread \
  -o $backupDir \
  -r 200000 \
  -F 256MiB &>> $logFile &

echo "dumpling start~, backup dir is [ $backupDir ]"
echo "You can execute the [ tail -f $logFile ] command to view the progress "
# check
sleep 3
ps -ef | grep dumpling | grep -Ev 'grep'
}

main(){
    init;
    mkDir
    dump;
    rmBackup
    
}

# run scripts
main;
