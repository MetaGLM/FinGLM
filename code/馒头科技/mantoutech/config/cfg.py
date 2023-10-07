import os

PDF_TEXT_DIR = 'pdf_docs'

# XPDF_PATH = r'C:\Program Files\Xpdf'

ERROR_PDF_DIR = 'error_pdfs'

CLASSIFY_PTUNING_PRE_SEQ_LEN = 512
KEYWORDS_PTUNING_PRE_SEQ_LEN = 256
NL2SQL_PTUNING_PRE_SEQ_LEN = 128
NL2SQL_PTUNING_MAX_LENGTH = 2200

if os.path.dirname(__file__).startswith('/home'):
    ONLINE = False
else:
    ONLINE = True


if ONLINE:
    NUM_PROCESSES = 12
    DATA_PATH = '/app/'
    CLASSIFY_CHECKPOINT_PATH ="/app/JamePeng_Ptuning_Classify0903/JamePeng_Ptuning_Classify/Fin-Train-chatglm2-6b-pt-512-2e-2/checkpoint-400/"
    NL2SQL_CHECKPOINT_PATH = "/app/Steve_NL2SQL/checkpoint-600/"
    KEYWORDS_CHECKPOINT_PATH = '/app/JamePeng_Keywords_0903/JamePeng_Keywords/Fin-Train-chatglm2-6b-pt-256-2e-2/checkpoint-250/'
    XPDF_PATH = '/app/xpdf/bin64'
else:
    NUM_PROCESSES = 32
    DATA_PATH = '/raidnvme/czc/OpenDataset/ChatGLM_FinTech/'

    if os.path.dirname(__file__).startswith('/home/jamepeng'):
        CLASSIFY_CHECKPOINT_PATH ="/home/jamepeng/git_projects/ChatGLM2-6B/ptuning_classify/output/Fin-Train-chatglm2-6b-pt-512-2e-2/checkpoint-200"
        KEYWORDS_CHECKPOINT_PATH = "/home/jamepeng/git_projects/ChatGLM2-6B/ptuning_keywords/output/JamePeng_Keywords/Fin-Train-chatglm2-6b-pt-256-2e-2/checkpoint-200"
        NL2SQL_CHECKPOINT_PATH = "/home/jamepeng/git_projects/ChatGLM2-6B/ptuning/output/JamePeng_NL2SQL/Fin-Train-chatglm2-6b-pt-2048-2e-2/checkpoint-250"
    else:
        CLASSIFY_CHECKPOINT_PATH ="/raidnvme/czc/OpenDataset/ChatGLM_FinTech/JamePeng_Ptuning_Classify0903/JamePeng_Ptuning_Classify/Fin-Train-chatglm2-6b-pt-512-2e-2/checkpoint-400/"
        # NL2SQL_CHECKPOINT_PATH = "/raidnvme/czc/OpenDataset/ChatGLM_FinTech/JamePeng_NL2SQL/Fin-Train-chatglm2-6b-pt-2048-2e-2/checkpoint-250/"
        # CLASSIFY_CHECKPOINT_PATH = '/raidnvme/czc/OpenDataset/ChatGLM_FinTech/JamePeng_Ptuning_Classify0902/Fin-Train-chatglm2-6b-pt-512-2e-2/checkpoint-200/'
        KEYWORDS_CHECKPOINT_PATH = '/raidnvme/czc/OpenDataset/ChatGLM_FinTech/JamePeng_Keywords_0903/JamePeng_Keywords/Fin-Train-chatglm2-6b-pt-256-2e-2/checkpoint-250/'
        NL2SQL_CHECKPOINT_PATH = "/raidnvme/czc/OpenDataset/ChatGLM_FinTech/Steve_NL2SQL/checkpoint-600/"
        XPDF_PATH = '/home/czc/Projects/fintechqa/xpdf/bin64'