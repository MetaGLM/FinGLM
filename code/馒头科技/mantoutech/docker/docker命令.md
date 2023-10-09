1. 删除容器
docker rm 容器id

2. 删除镜像
docker rmi 镜像id

3. 停止容器
docker stop 容器id

4. 执行镜像, 使用--rm参数会在容器退出后，自动删除容器实例
docker run --gpus all -it 镜像id /bin/bash

5. 进入容器
docker exec -it 容器id /bin/bash

或者docker restart 容器id
加上 docker attach 容器id

6. 退出容器Crl+P+Q

7. 提交容器
docker commit b19df93c8b1a registry.cn-hangzhou.aliyuncs.com/mantoukeji/mantoukeji:testcu113

8. push容器
docker push XXX

9. docker拷贝文件 
docker cp src containerid:dst
docker cp . contrainerid:dst 拷贝目录下面全部文件

# 测试
docker run XXX sh run.sh

docker资料
https://yeasy.gitbook.io/docker_practice/image/dockerfile/workdir

docker网址
https://cr.console.aliyun.com/repository/cn-hangzhou/mantoukeji/mantoukeji/images?accounttraceid=e97eb035a1634037a452f8a5485bbbe0xfif