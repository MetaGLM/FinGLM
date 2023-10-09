#!/bin/bash

# 以下命令作为打包示例，实际使用时请修改为自己的镜像地址, 建议每次提交前完成版本修改重新打包
docker build -t registry.cn-shanghai.aliyuncs.com/finglm/fingpt:v1 . 
