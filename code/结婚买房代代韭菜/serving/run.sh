# nvidia-smi

# 构建db
python build_db.py

if [[ $? -ne 0 ]]; then
    echo "build db failed."
    exit
fi

# 预估
python predict.py --mode all_model
