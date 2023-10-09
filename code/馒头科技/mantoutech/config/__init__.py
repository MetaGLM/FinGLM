import os
os.environ['SENTENCE_TRANSFORMERS_HOME'] = '/raidnvme/czc/SENTENCE_TRANSFORMERS_HOME'

# for huggingface
if os.path.dirname(__file__).startswith('/home'):
    os.environ['HF_HOME'] = '/raidnvme/czc/HF_HOME'

# for modelscope
os.environ['CACHE_HOME'] = '/raidnvme/czc/MODELSCOPE_CACHE_HOME'
