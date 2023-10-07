## default
train
```python
# 方式1
git clone http://www.modelscope.cn/datasets/modelscope/chatglm_llm_fintech_raw_dataset.git

# 方式2
from modelscope.msdatasets import MsDataset
ds =  MsDataset.load('modelscope/chatglm_llm_fintech_raw_dataset', subset_name='default', split='train', use_streaming=True)
for item in ds:
    print(item)
    
```

