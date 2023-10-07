#!/bin/bash

# 以下命令作为打包示例，实际使用时请修改为自己的镜像地址, 建议每次提交前完成版本修改重新打包
docker build -t registry.cn-hangzhou.aliyuncs.com/mantoukeji/mantoukeji:812runsh  . 
docker push registry.cn-hangzhou.aliyuncs.com/mantoukeji/mantoukeji:812runsh