import pandas as pd
import pandasql as ps
import numpy as np

from pandasql import sqldf, load_meat, load_births

pysqldf = lambda q: sqldf(q, globals())

meat = load_meat()

print(meat.head())

births = load_births()

print(pysqldf("SELECT * FROM meat LIMIT 10;").head())