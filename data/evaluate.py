# coding=utf-8
import json
import sys
import re
from text2vec import SentenceModel, semantic_search, Similarity

# 错误字典，这里只是示例
error_msg = {
    'TextEncodeInput must be Union[TextInputSequence, Tuple[InputSequence, InputSequence]]': "answer format error",
}


def dump_2_json(info, path):
    with open(path, 'w') as output_json_file:
        json.dump(info, output_json_file)


def report_error_msg(detail, showMsg, out_p):
    error_dict = dict()
    error_dict['errorDetail'] = detail
    error_dict['errorMsg'] = showMsg
    error_dict['score'] = 0
    error_dict['scoreJson'] = {}
    error_dict['success'] = False
    dump_2_json(error_dict, out_p)


def report_score(score, scorejson, out_p):
    result = dict()
    result['success'] = True
    result['score'] = score

    # 这里{}里面的score注意保留，但可以增加其他key，比如这样：
    # result['scoreJson'] = {'score': score, 'aaaa': 0.1}
    result['scoreJson'] = scorejson

    dump_2_json(result, out_p)


class countScore():
    def __init__(self):
        self.sys_path = standard_path  # 答案文件路径
        self.simModel_path = 'text2vec-base-chinese'  # 相似度模型路径
        self.simModel = SentenceModel(model_name_or_path=self.simModel_path, device='cuda:0')
        self.sys_data_list = [json.loads(line.replace('\n', '')) for line in
                              open(self.sys_path, 'r', encoding='utf-8').readlines() if line != '\n']
        self.type1IdList = [dt['id'] for dt in self.sys_data_list if dt['type'] == '1']
        self.type12IdList = [dt['id'] for dt in self.sys_data_list if dt['type'] == '1-2']
        self.type2IdList = [dt['id'] for dt in self.sys_data_list if dt['type'] == '2-1']
        self.type22IdList = [dt['id'] for dt in self.sys_data_list if dt['type'] == '2-2']
        self.type31IdList = [dt['id'] for dt in self.sys_data_list if dt['type'] == '3-1']
        self.type32IdList = [dt['id'] for dt in self.sys_data_list if dt['type'] == '3-2']
        self.sys_data_type1_list = [tmp_line for tmp_line in self.sys_data_list if tmp_line['type'] == '1']
        self.sys_data_type1_question_list = [tmp_line['question'] for tmp_line in self.sys_data_list if
                                             tmp_line['type'] == '1']
        self.sys_data_type12_list = [tmp_line for tmp_line in self.sys_data_list if tmp_line['type'] == '1-2']
        self.sys_data_type12_question_list = [tmp_line['question'] for tmp_line in self.sys_data_list if
                                              tmp_line['type'] == '1-2']
        self.sys_data_type2_list = [tmp_line for tmp_line in self.sys_data_list if tmp_line['type'] == '2-1']
        self.sys_data_type2_question_list = [tmp_line['question'] for tmp_line in self.sys_data_list if
                                             tmp_line['type'] == '2-1']
        self.sys_data_type22_list = [tmp_line for tmp_line in self.sys_data_list if tmp_line['type'] == '2-2']
        self.sys_data_type22_question_list = [tmp_line['question'] for tmp_line in self.sys_data_list if
                                              tmp_line['type'] == '2-2']
        self.sys_data_type31_list = [tmp_line for tmp_line in self.sys_data_list if tmp_line['type'] == '3-1']
        self.sys_data_type31_question_list = [tmp_line['question'] for tmp_line in self.sys_data_list if
                                              tmp_line['type'] == '3-1']
        self.sys_data_type32_list = [tmp_line for tmp_line in self.sys_data_list if tmp_line['type'] == '3-2']
        self.sys_data_type32_question_list = [tmp_line['question'] for tmp_line in self.sys_data_list if
                                              tmp_line['type'] == '3-2']

    def check_type1(self, per_data_type1_list):
        score_type1 = 0
        for i in range(len(self.sys_data_type1_list)):
            per_data_json = per_data_type1_list[i]
            sys_data_json = self.sys_data_type1_list[i]
            prompt = sys_data_json['prompt']
            sys_answer = [x.replace(',', '').replace(' ', '') for x in sys_data_json['answer']]
            per_answer = per_data_json['answer'].replace(',', '').replace(' ', '')
            key_word = prompt['key_word']
            year = prompt['year']
            if key_word != '无|不|没有|未|否|非|莫|抱歉|毋':
                key_value = prompt[key_word].replace(',', '').replace(' ', '')
                if key_value in per_answer:
                    score_type1 += 0.25
                    score_type1 += \
                    semantic_search(self.simModel.encode([per_answer]), self.simModel.encode(sys_answer), top_k=1)[0][
                        0]['score'] * 0.5
                    if key_word in per_answer and year in per_answer:
                        score_type1 += 0.25
            else:
                key_word_list = key_word.split('|')
                Flag = False
                for kword in key_word_list:
                    if kword in per_answer:
                        Flag = True
                        break
                if Flag is True:
                    score_type1 += 0.25
                    score_type1 += \
                    semantic_search(self.simModel.encode([per_answer]), self.simModel.encode(sys_answer), top_k=1)[0][
                        0]['score'] * 0.5
                    if year in per_answer:
                        score_type1 += 0.25

        return score_type1

    def check_type12(self, per_data_type12_list):
        score_type12 = 0
        for i in range(len(self.sys_data_type12_list)):
            per_data_json = per_data_type12_list[i]
            sys_data_json = self.sys_data_type12_list[i]
            sys_answer = [x.replace(',', '').replace(' ', '') for x in sys_data_json['answer']]
            per_answer = per_data_json['answer'].replace(',', '').replace(' ', '')
            prompt = sys_data_json['prompt']
            year = prompt['year']
            key_word = prompt['key_word']
            if key_word != '无|不|没有|未|否|非|莫|抱歉|毋':
                key_word_list = prompt['key_word'].split('、')

                tmp_value_count = 0
                tmp_key_count = 0

                for key_word in key_word_list:
                    if prompt[key_word].replace(',', '').replace(' ', '') in per_answer:
                        tmp_value_count += 1

                    if key_word in per_answer:
                        tmp_key_count += 1

                if tmp_value_count == len(key_word_list):
                    score_type12 += 0.25
                    score_type12 += \
                    semantic_search(self.simModel.encode([per_answer]), self.simModel.encode(sys_answer), top_k=1)[0][
                        0]['score'] * 0.5
                    if tmp_key_count == len(key_word_list) and year in per_answer:
                        score_type12 += 0.25
            else:
                key_word_list = key_word.split('|')
                Flag = False
                for kword in key_word_list:
                    if kword in per_answer:
                        Flag = True
                        break
                if Flag is True:
                    score_type12 += 0.25
                    score_type12 += \
                    semantic_search(self.simModel.encode([per_answer]), self.simModel.encode(sys_answer), top_k=1)[0][
                        0]['score'] * 0.5
                    if year in per_answer:
                        score_type12 += 0.25

        return score_type12

    def check_type2(self, per_data_type2_list):
        score_type2 = 0

        for i in range(len(self.sys_data_type2_list)):
            per_data_json = per_data_type2_list[i]
            sys_data_json = self.sys_data_type2_list[i]

            sys_answer = [x.replace(',', '').replace(' ', '') for x in sys_data_json['answer']]
            per_answer = per_data_json['answer'].replace(',', '').replace(' ', '')
            prompt = sys_data_json['prompt']
            year = prompt['year']
            key_word = prompt['key_word']

            if key_word != '无|不|没有|未|否|非|莫|抱歉|毋':
                key_word_list = prompt['key_word'].split('、')
                key_value = prompt['prom_answer'].replace(',', '').replace(' ', '')

                tmp_key_count = 0
                tmp_key_value_count = 0
                for key_word in key_word_list:
                    if key_word in per_answer:
                        tmp_key_count += 1

                    if prompt[key_word].replace(',', '').replace(' ', '') in per_answer:
                        tmp_key_value_count += 1

                tmp_count = tmp_key_count + tmp_key_value_count

                if key_value in per_answer:
                    score_type2 += 0.25
                    score_type2 += \
                    semantic_search(self.simModel.encode([per_answer]), self.simModel.encode(sys_answer), top_k=1)[0][
                        0]['score'] * 0.5
                    if tmp_count == len(key_word_list) * 2 and year in per_answer:
                        score_type2 += 0.25
            else:
                key_word_list = key_word.split('|')
                Flag = False
                for kword in key_word_list:
                    if kword in per_answer:
                        Flag = True
                        break
                if Flag is True:
                    score_type2 += 0.25
                    score_type2 += \
                    semantic_search(self.simModel.encode([per_answer]), self.simModel.encode(sys_answer), top_k=1)[0][
                        0]['score'] * 0.5
                    if year in per_answer:
                        score_type2 += 0.25
        return score_type2

    def check_type22(self, per_data_type22_list):
        score_type22 = 0

        for i in range(len(self.sys_data_type22_list)):
            per_data_json = per_data_type22_list[i]
            sys_data_json = self.sys_data_type22_list[i]
            sys_answer = [x.replace(',', '').replace(' ', '') for x in sys_data_json['answer']]
            per_answer = per_data_json['answer'].replace(',', '').replace(' ', '')

            prompt = sys_data_json['prompt']
            key_word = prompt['key_word']
            year = prompt['year']

            if key_word != '无|不|没有|未|否|非|莫|抱歉|毋':
                key_word_list = prompt['key_word'].split('、')
                key_value = prompt['prom_answer'].replace(',', '').replace(' ', '')

                tmp_count = 0
                for key_word in key_word_list:
                    if prompt[key_word].replace(',', '').replace(' ', '') in per_answer:
                        tmp_count += 1

                if key_value == '相同' and key_value in per_answer and '不相同' not in per_answer:
                    score_type22 += 0.25
                    score_type22 += \
                    semantic_search(self.simModel.encode([per_answer]), self.simModel.encode(sys_answer), top_k=1)[0][
                        0]['score'] * 0.5
                    if tmp_count == len(key_word_list):
                        score_type22 += 0.25
                elif key_value == '不相同' and key_value in per_answer:
                    score_type22 += 0.25
                    score_type22 += \
                    semantic_search(self.simModel.encode([per_answer]), self.simModel.encode(sys_answer), top_k=1)[0][
                        0]['score'] * 0.5
                    if tmp_count == len(key_word_list):
                        score_type22 += 0.25
            else:
                key_word_list = key_word.split('|')
                Flag = False
                for kword in key_word_list:
                    if kword in per_answer:
                        Flag = True
                        break
                if Flag is True:
                    score_type22 += 0.25
                    score_type22 += \
                    semantic_search(self.simModel.encode([per_answer]), self.simModel.encode(sys_answer), top_k=1)[0][
                        0]['score'] * 0.5
                    if year in per_answer:
                        score_type22 += 0.25
        return score_type22

    def check_type31(self, per_data_type31_list):
        score_type31 = 0

        for i in range(len(self.sys_data_type31_list)):
            per_data_json = per_data_type31_list[i]
            sys_data_json = self.sys_data_type31_list[i]

            sys_answer = [x.replace(',', '').replace(' ', '') for x in sys_data_json['answer']]
            per_answer = per_data_json['answer'].replace(',', '').replace(' ', '')
            year = sys_data_json['prompt']['year']
            key_word = sys_data_json['prompt']['key_word']
            if key_word == '':
                score_type31 += \
                semantic_search(self.simModel.encode([per_answer]), self.simModel.encode(sys_answer), top_k=1)[0][0][
                    'score']
            elif key_word == '无|不|没有|未|否|非|莫|抱歉|毋':
                key_word_list = key_word.split('|')
                Flag = False
                for kword in key_word_list:
                    if kword in per_answer:
                        Flag = True
                        break
                if Flag is True:
                    score_type31 += 0.25
                    score_type31 += \
                    semantic_search(self.simModel.encode([per_answer]), self.simModel.encode(sys_answer), top_k=1)[0][0]['score'] * 0.5
                    if year in per_answer:
                        score_type31 += 0.25
            else:
                key_word_list = key_word.split('、')
                key_length = len(key_word_list)
                tm_len = 0
                for t_key in key_word_list:
                    if re.search(t_key, per_answer):
                        tm_len += 1
                if tm_len == key_length:
                    score_type31 += 0.25
                    score_type31 += semantic_search(self.simModel.encode([per_answer]), self.simModel.encode(sys_answer), top_k=1)[0][0]['score'] * 0.75
                else:
                    score_type31 += semantic_search(self.simModel.encode([per_answer]), self.simModel.encode(sys_answer), top_k=1)[0][0]['score'] * 0.75

        return score_type31

    def check_type32(self, per_data_type32_list):
        score_type32 = 0

        for i in range(len(self.sys_data_type32_list)):
            per_data_json = per_data_type32_list[i]
            sys_data_json = self.sys_data_type32_list[i]

            sys_answer = [x.replace(',', '').replace(' ', '') for x in sys_data_json['answer']]
            per_answer = per_data_json['answer'].replace(',', '').replace(' ', '')
            score_type32 += \
            semantic_search(self.simModel.encode([per_answer]), self.simModel.encode(sys_answer), top_k=1)[0][0][
                'score']

        return score_type32

    def count(self, Per_path):
        per_data_list = [json.loads(line.replace('\n', '')) for line in
                         open(Per_path, 'r', encoding='utf-8').readlines() if line != '\n']
        answer_empty_count = 0
        for p_data_json in per_data_list:
            if isinstance(p_data_json['answer'], list):
                raise ValueError('The type of answer must be list')
            elif len(p_data_json['answer']) == 0:
                answer_empty_count += 1
        if len(per_data_list) != len(self.sys_data_list):
            raise ValueError('The length of your data is not correct')
        elif answer_empty_count == len(self.sys_data_list):
            raise ValueError('All your answers are empty')
        else:
            per_data_type1_list = [tmp_line for tmp_line in per_data_list if
                                   tmp_line['id'] in self.type1IdList and tmp_line[
                                       'question'] in self.sys_data_type1_question_list]
            per_data_type12_list = [tmp_line for tmp_line in per_data_list if
                                    tmp_line['id'] in self.type12IdList and tmp_line[
                                        'question'] in self.sys_data_type12_question_list]
            per_data_type2_list = [tmp_line for tmp_line in per_data_list if
                                   tmp_line['id'] in self.type2IdList and tmp_line[
                                       'question'] in self.sys_data_type2_question_list]
            per_data_type22_list = [tmp_line for tmp_line in per_data_list if
                                    tmp_line['id'] in self.type22IdList and tmp_line[
                                        'question'] in self.sys_data_type22_question_list]
            per_data_type31_list = [tmp_line for tmp_line in per_data_list if
                                    tmp_line['id'] in self.type31IdList and tmp_line[
                                        'question'] in self.sys_data_type31_question_list]
            per_data_type32_list = [tmp_line for tmp_line in per_data_list if
                                    tmp_line['id'] in self.type32IdList and tmp_line[
                                        'question'] in self.sys_data_type32_question_list]

            if len(per_data_type1_list) != len(self.sys_data_type1_list) or \
                    len(per_data_type12_list) != len(self.sys_data_type12_list) or \
                    len(per_data_type2_list) != len(self.sys_data_type2_list) or \
                    len(per_data_type22_list) != len(self.sys_data_type22_list) or \
                    len(per_data_type31_list) != len(self.sys_data_type31_list) or \
                    len(per_data_type32_list) != len(self.sys_data_type32_list):
                raise ValueError('Your data location is inconsistent with the source data')
            else:
                type1Score = self.check_type1(per_data_type1_list)
                type12Score = self.check_type12(per_data_type12_list)
                type2Score = self.check_type2(per_data_type2_list)
                type22Score = self.check_type22(per_data_type22_list)
                type31Score = self.check_type31(per_data_type31_list)
                type32Score = self.check_type32(per_data_type32_list)

                Score1 = round((type1Score + type12Score) / (len(self.type1IdList) + len(self.type12IdList)) * 100, 4)
                Score2 = round((type2Score + type22Score) / (len(self.type2IdList) + len(self.type22IdList)) * 100, 4)
                Score3_1 = round(type31Score / len(self.type31IdList) * 100, 4)
                Score3_2 = round(type32Score / len(self.type32IdList) * 100, 4)

                Score_dict = {'type1Score': Score1, 'type2Score': Score2, 'type3-1Score': Score3_1,
                              'type3-2Score': Score3_2}

                finalScore = round((Score1 * 0.3 + Score2 * 0.4 + Score3_1 * 0.2 + Score3_2 * 0.1), 4)
                Score_dict['score'] = finalScore

                return finalScore, Score_dict


if __name__ == "__main__":
    '''
      online evaluation

    '''
    in_param_path = sys.argv[1]
    out_path = sys.argv[2]
    # in_param_path = 'input_param.json'
    # out_path = 'output.json'

    # read submit and answer file from first parameter
    with open(in_param_path, 'r') as load_f:
        input_params = json.load(load_f)

    # 标准答案路径
    standard_path = input_params["fileData"]["standardFilePath"]
    print("Read standard from %s" % standard_path)

    # 选手提交的结果文件路径
    submit_path = input_params["fileData"]["userFilePath"]
    print("Read user submit file from %s" % submit_path)

    try:
        score, score_json = countScore().count(submit_path)
        report_score(score, score_json, out_path)
    except Exception as e:
        if str(e.args) in error_msg:
            report_error_msg(error_msg[str(e.args)], error_msg[str(e.args)], out_path)
        else:
            report_error_msg(str(e.args), str(e.args), out_path)

