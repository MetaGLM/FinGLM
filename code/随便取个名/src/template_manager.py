from langchain import PromptTemplate

class TemplateManager:
    def __init__(self):
        self.templates = {
            # special key
            0 : PromptTemplate(
                input_variables=["question"],
                template="假设你是金融专家，请简洁和专业的来回答问题：{question}\n答："
            ),
            # basis_info_keys
            1 : PromptTemplate(
                input_variables=["prompt", "question"],
                template="根据已知信息中简洁和专业的来回答问题，\n问题是：{question}\n已知信息：{prompt}\n答："
            ),
            # ratio_keys
            2 : PromptTemplate(
                input_variables=["prompt", "question"],
                template="根据已知信息专业的来回答问题，请结合已知信息的计算公式作为答案。\n问题是：{question}\n已知信息：{prompt}\n答："
            ),
            # finacial_keys
            3 : PromptTemplate(
                input_variables=["prompt", "question"],
                template="根据已知信息中简洁和专业的来回答问题，\n问题是：{question}\n已知信息：{prompt}\n答："
            ),
            # analysis_keys
            4 : PromptTemplate(
                input_variables=["prompt", "question"],
                template ="根据背景知识，简洁和专业的来回答问题，\n"
                        "【背景知识】：{prompt}\n"
                        "【问题】：{question}\n答："
            ),
            # sql_keys
            5 : PromptTemplate(
                input_variables=["prompt", "question"],
                template="根据已知信息中简洁和专业的来回答问题，\n问题是：{question}\n已知信息：{prompt}\n答："
            ),
        }

    def get_template(self, template_name):
        return self.templates.get(template_name, None)

template_manager = TemplateManager()