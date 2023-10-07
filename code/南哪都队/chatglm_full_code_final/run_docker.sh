sh build.sh
docker container prune -f
docker rmi -f `docker images | grep '<none>'| awk '{print $3}'`
docker run -m 20g --cpus=8 -v /extend/fintech/recover/app/data:/tcdata -v /extend/fintech/recover/app/result:/tmp --gpus 1 -it registry.cn-shanghai.aliyuncs.com/finglm/fingpt:v1 