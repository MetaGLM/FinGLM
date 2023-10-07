#!/bin/bash
#
#SBATCH -N 1 ### 使用的节点数目
#SBATCH -n 8 ### 一个节点内部的 20 个核
#SBATCH -p node
#SBATCH --gres=gpu:2 ### 使用 2 张 gpu 卡
#SBATCH --nodelist=gpu001 ### 使用 gpu001 节点
#SBATCH --partition=intelgpu80g ### PARTITION 名称，可通过 sinfo 查询
#SBATCH --job-name=test1 ### 提交的任务名称
#SBATCH --output=./log.log ### 输出文件
#SBATCH --error=./err.log ### 错误日志文件
### 使用的 gpu 卡数，与–gres=gpu:4 的数字一致
NP=$((4))
### 执行任务所需要加载的模块
module load oneapi22.3
module load vasp/vasp6.3.0_nv
### 一些提示性输出
export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1
export MV2_ENABLE_AFFINITY=0
echo ”The current job ID is $SLURM_JOB_ID”
echo ”Running on $SLURM_JOB_NUM_NODES nodes:”
echo $SLURM_JOB_NODELIST
echo ”Using $SLURM_NTASKS_PER_NODE tasks per node”
echo ”A total of $SLURM_NTASKS tasks is used”
### 对任务执行的内存不做限制
ulimit -s unlimited
ulimit -c unlimited
### 加载任务所需要的库
export LD_LIBRARY_PATH=/usr/local/lib64:$LD_LIBRARY_PATH
echo $LD_LIBRARY_PATH
### 执行任务
# sh run.sh
sh train.sh
# python main.py