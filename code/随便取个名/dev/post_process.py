import os
import re
import sys
import json
import shutil
from collections import defaultdict

def main():
    results = []
    with open('output/generated_predictions.json', 'r', encoding='utf-8') as f1, open('data/dataset.json', 'r', encoding='utf-8') as f2:
        for line, answer in zip(f1.readlines(),f2.readlines()):
            result = json.loads(line)
            dataset = json.loads(answer)
            if dataset['category'] in [1, 2, 3, 5] and dataset['prompt'] != '':
                result['answer'] = dataset['prompt']
                
            results.append(result)
    with open('output.json', 'w', encoding='utf-8') as f:
        for result in results:
            f.write(json.dumps(result, ensure_ascii=False)+'\n')
    
    shutil.copy2('./output.json', '/tmp/result.json')
    
if __name__ == '__main__':
    main()
    