
## 数据准备
### /data/code/app：FinGLM/code/Chatglm反卷总局/app
### /data/tcdata:
![image](https://github.com/MetaGLM/FinGLM/assets/34187337/78d39d09-a288-4645-aa43-f1181598b2a1)


## 安装docker和nvidia-docker
参考百度

## docker拉取镜像
```bash
docker pull registry.cn-shanghai.aliyuncs.com/fjzj/chatglm_fjzj:v6
```

## docker执行
```bash
docker run -it -v /data/tcdata:/tcdata -v /data/code/app:/app -it registry.cn-shanghai.aliyuncs.com/fjzj/chatglm_fjzj:v6
```

## 进入docker环境
```bash
docker ps
docker attach [contain-id]
```

## 运行
```bash
./run.sh
```

