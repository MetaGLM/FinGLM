import os


if os.name == "nt":
    # vector search
    VECTOR_CACHE_PATH = "E:\\vector_search_cache"
    ENCODER_MODEL_PATH = "models/encoder_models/GanymedeNil_text2vec-large-chinese"
    ENCODER_NORMALIZE_EMBEDDINGS = True
    VECTOR_SEARCH_THRESHOLD_1 = 0.35 # for comp_name etc
    VECTOR_SEARCH_THRESHOLD_2 = -100 # for nodes or doc

    # chatglm2
    LLM_NAME = "D:\LLM\chatglm2-6b-docker\chatglm2-6b"
    LLM_CACHE_DIR= "D:\\LLM"
    LLM_REVISION = 'v1.0.7'

    # data
    HTML_PATH = "./test_data/allhtml"
    PDF_PATH = "D:\\data\\chatglm_llm_fintech_raw_dataset\\allpdf"
    PDF_IDX_PATH = "./test_data/C-list-pdf-name.txt"
    TXT_PATH = "D:\\data\\chatglm_llm_fintech_raw_dataset\\alltxt"
    STOPWORDS_PATH = "fin_qa/resources/stopwords.txt"
    QUESTION_PATH = "./test_data/C-list-question.json"
    OUTPUT_PATH = "result.json"

    # DB

    DB_PATH = "db/test.db"

    # prefix_encoder
    ROUTER_PRE_SEQ_LEN = 16
    ROUTER_CHECKPOINT_PATH = "./prefix_encoder/router"

    NL2SQL_PRE_SEQ_LEN = 256
    NL2SQL_CHECKPOINT_PATH = "./prefix_encoder/nl2sql"

    NORMALIZE_PRE_SEQ_LEN = 256
    NORMALIZE_CHECKPOINT_PATH = "./prefix_encoder/normalize"

    # tmp
    ROUTER_FILE_PATH = "./test_data/router.json"
    SQL_FILE_PATH = "./test_data/sql.json"
    NORM_SOLVED_PATH = "./test_data/normed.json"
else:
    # vector search
    VECTOR_CACHE_PATH = "./vector_search_cache"
    ENCODER_MODEL_PATH = "/models/encoder_models/GanymedeNil_text2vec-large-chinese"
    ENCODER_NORMALIZE_EMBEDDINGS = True
    VECTOR_SEARCH_THRESHOLD_1 = 0.35 # for comp_name etc
    VECTOR_SEARCH_THRESHOLD_2 = -100 # for nodes or doc

    # chatglm2
    LLM_NAME = "/tcdata/chatglm2-6b-hug"
    # LLM_NAME = "/tcdata/chatglm2-6b"
    LLM_CACHE_DIR= "D:\\LLM"
    LLM_REVISION = 'v1.0.7'

    # data
    HTML_PATH = "/tcdata/allhtml"
    PDF_PATH = "/tcdata/allpdf"
    PDF_IDX_PATH = "/tcdata/C-list-pdf-name.txt"
    TXT_PATH = "/tcdata/alltxt"
    STOPWORDS_PATH = "./resources/stopwords.txt"
    QUESTION_PATH = "/tcdata/C-list-question.json"
    OUTPUT_PATH = "/tmp/result.json"

    # DB
    DB_PATH = "/db/online.db"

    # prefix_encoder
    ROUTER_PRE_SEQ_LEN = 16
    ROUTER_CHECKPOINT_PATH = "/prefix_encoder/router"

    NL2SQL_PRE_SEQ_LEN = 256
    NL2SQL_CHECKPOINT_PATH = "/prefix_encoder/nl2sql"

    NORMALIZE_PRE_SEQ_LEN = 256
    NORMALIZE_CHECKPOINT_PATH = "/prefix_encoder/normalize"

    # tmp
    ROUTER_FILE_PATH = "./test_data/router.json"
    SQL_FILE_PATH = "./test_data/sql.json"
    NORM_SOLVED_PATH = "./test_data/normed.json"