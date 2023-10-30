# Training
0. Change dir to training
```
cd training
```

1. Install requirements
```
pip install -r requirements.txt
```

2. Train your modles use your custom dataset
```
cd ptuning
# modify training scripts to adapt your configs
bash train_router.sh
# bash train_nl2sql.sh
# bash train_normalize.sh
```

# Serving
0. Change dir to training
```
cd serving
```

1. Install requirements
```
pip install -r requirements.txt
```

2. Copy your tuned models to prefix_encoder
```
cp -r xxx prefix_encoder
```

3. Run your app
```
bash run.sh
```

# Tuned models weights
[modelscope](https://modelscope.cn/models/getmarried_buyahouse_beingleeks4ever/SMP2023_gbb4/files)