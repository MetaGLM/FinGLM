import pandas as pd

from configs.model_config import item_to_parten_path
class TrieNode:
    def __init__(self):
        self.children = {}
        self.end_of_word = False

class KeywordMapping:

    def __init__(self, patterns, key_to_parten) -> None:
        self.partens = patterns
        self.key_to_parten = key_to_parten
        self.time_list = ['2019', '2020', '2021']

    def add_word(self, root, word):
        node = root
        for char in word:
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
        node.end_of_word = True

    def search(self, root, sentence):
        res = []
        length = len(sentence)
        i = 0
        while i < length:
            if sentence[i] in root.children:  # 判断子节点中是否有该字符
                j = i
                node = root
                match = None
                while j < length and sentence[j] in node.children:
                    node = node.children[sentence[j]]
                    if node.end_of_word:
                        match = sentence[i: j + 1]  # 当前匹配成功的字符串
                    j += 1
                if match:
                    # print(match)
                    # print(i)
                    i += len(match) - 1  # 下一次匹配的起始位置
                    res.append(match)  # 添加到结果中
            i += 1
            # print('new i :', i)
        return res

    def keyword_matching(self, keywords, sentence):
        root = TrieNode()
        for word in keywords:
            self.add_word(root, word)
        return self.search(root, sentence)
    
    def question_to_keywords(self, question):
        question = question.replace('的', '')
        flag = False
        ##判断问题中是否包含['2019', '2020', '2021']中的一个
        for ntime in self.time_list:
            if ntime in question:
                flag = True
                break
        if flag is False:
            return question
        key_words = self.keyword_matching(self.partens, question)
        if len(key_words) > 0:
            for idx, key_word in enumerate(key_words):
                key_words[idx] = self.key_to_parten[key_word][0]
            key_words = ' '.join(key_words)
            return key_words
        else:
            return question
    
    def question_to_keywords_with_raw_words(self, question):
        question = question.replace('的', '')
        flag = False
        ##判断问题中是否包含['2019', '2020', '2021']中的一个
        for ntime in self.time_list:
            if ntime in question:
                flag = True
                break
        if flag is False:
            return question, []
        key_words = self.keyword_matching(self.partens, question)
        raw_words = []
        if len(key_words) > 0:
            for idx, key_word in enumerate(key_words):
                raw_words.append(key_to_parten[key_word][1])    
                key_words[idx] = self.key_to_parten[key_word][0]
            key_words = ' '.join(key_words)
            return key_words, raw_words
        else:
            return question, []


item_to_parten = pd.read_csv(item_to_parten_path)
keys = item_to_parten['key'].tolist()
values = item_to_parten['parten'].tolist()
raw_keys = item_to_parten['raw_key'].tolist()

key_to_parten = {key: [value, raw_key] for key, value, raw_key in zip(keys, values, raw_keys)}

# 把item_to_parten转换成字典
query_keyword_map = KeywordMapping(keys, key_to_parten)
