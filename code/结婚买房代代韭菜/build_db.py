from db.build_db_from_dt import build_db
from db.db_utils import query_single_klg, get_tables

if __name__ == "__main__":
    build_db()



    # 测试
    # import sqlite3
    # db = sqlite3.connect("../db/test.db")
    # cursor = db.cursor()