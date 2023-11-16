from langchain.agents import AgentType, load_tools, initialize_agent
from langchain.agents import AgentExecutor, create_sql_agent
from langchain.agents.agent_toolkits import SQLDatabaseToolkit
from langchain.utilities import SQLDatabase
from langchain.llms import ChatGLM
from langchain_experimental.sql import SQLDatabaseChain
from langchain.chains import create_sql_query_chain


endpoint_url = ("http://127.0.0.1:29501")

# direct access endpoint in a proxied environment
# os.environ['NO_PROXY'] = '127.0.0.1'

llm = ChatGLM(
    endpoint_url=endpoint_url,
    max_token=10000,
    history=[],
    temperature=0.7,
    # top_p=0.9,
    model_kwargs={"sample_model_args": False},
)



from langchain.prompts import PromptTemplate

TEMPLATE = """给定一个输入问题，首先创建一个语法正确的 SQLite语句 查询来运行，然后查看查询结果并返回答案。使用以下格式:

问题: “这里是问题”
SQLQuery: “要运行的 SQL 查询”

Only use the following tables:

问题: {input}"""

CUSTOM_PROMPT = PromptTemplate(
    input_variables=["input"], template=TEMPLATE
)

# 使用相对路径
db = SQLDatabase.from_uri("sqlite:///data/company.db")
chain = create_sql_query_chain(llm=llm, db=db)

db_chain = SQLDatabaseChain.from_llm(llm, db, verbose=True)

while True:
    i = input()
    db_chain.run("在debt表中，2019-2021年哪些上市公司货币资金均位列前十？")
    # response = chain.invoke({"question":"专业的写出SQL语句：在debt表中，2019-2021年哪些上市公司货币资金均位列前十？"})
    # print(response)
    # print(db.run(response))