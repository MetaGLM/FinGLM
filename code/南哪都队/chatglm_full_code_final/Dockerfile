# FROM registry.cn-shanghai.aliyuncs.com/tcc-public/pytorch:2.0.0-py3.9.12-cuda11.8.0-u22.04
FROM registry.cn-shanghai.aliyuncs.com/tcc-public/pytorch:1.12-py3.9.12-cuda11.3.1-u20.04


# 如有安装其他软件的需求
RUN apt-get update && apt-get install curl

COPY requirements.txt /app/

RUN pip3 install -r /app/requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 复制代码到镜像仓库
COPY data /app/data
COPY templates /app/templates
COPY excel_extraction /app/excel_extraction
COPY finetune /app/finetune
COPY glm_components /app/glm_components
COPY model /app/model
COPY *.* /app

# 指定工作目录
WORKDIR /app

# 容器启动运行命令
CMD ["bash", "run.sh"]