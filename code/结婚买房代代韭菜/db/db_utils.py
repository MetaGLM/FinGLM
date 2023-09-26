from db.db_config import *
from db.db_schema import *
from app.utils import algin_float_string
from app.keywords import short_comp_dict


def create_table(cursor):
    columns = "\n".join([
        f"{schema_zh2py[zh]} TEXT," for zh in schema_meta
    ]) + "\n".join([
        f"{schema_zh2py[zh]} TEXT," for zh in schema_base
    ]) + "\n".join([
        f"{schema_zh2py[zh]} REAL," for zh in schema_fin
    ]) + "\n".join([
        f"{schema_zh2py[zh]} INTEGER," for zh in schema_emp
    ])

    # columns = "\n".join([
    #     f"{schema_zh2py[zh]} TEXT," for zh in schema_meta
    # ]) + "\n".join([
    #     f"{schema_zh2py[zh]} TEXT," for zh in schema_base
    # ]) + "\n".join([
    #     f"{schema_zh2py[zh]} TEXT," for zh in schema_fin
    # ]) + "\n".join([
    #     f"{schema_zh2py[zh]} TEXT," for zh in schema_emp
    # ])
    
    ddl = f'''
    CREATE TABLE {TABLE_NAME} (
        {columns[:-1]}
    );
    '''
    # print(ddl)
    cursor.execute(ddl)

def get_tables(cursor):
    sql = """SELECT name FROM sqlite_master WHERE type='table';"""
    res = cursor.execute(sql).fetchone()
    if res == None:
        return []
    return res[0]

def gen_row(line):
    return ", ".join([repr(i) for i in line])

def insert_data(db, cursor, data):
    data_str = ",".join([f"({gen_row(line)})" for line in data])
    sql = f"""
    INSERT INTO {TABLE_NAME} VALUES
        {data_str}
    """
    # print(sql)
    cursor.execute(sql)
    db.commit()

def query_single_klg(cursor, table_name, comp, year, keyword):
    # print("##", keyword.word, keyword.raw_word)
    if comp in short_comp_dict:
        comp = short_comp_dict[comp]
    sql = f"""
    SELECT xiao_shu_wei_shu, gu_piao_jian_cheng, {schema_zh2py[keyword.word]}
    FROM {table_name}
    WHERE
        gong_si_ming_cheng = "{comp}"
        AND nian_fen = "{year}"
    """
    unit = "元" if keyword.word in schema_fin else ""
    unit = "人" if keyword.word in schema_emp else unit
    try:
        ret = cursor.execute(sql).fetchone()
        if not ret:
            return ""
        dot_bits = ret[0]
        abb = ret[1]
        val = ret[2]

        # if keyword.word in schema_fin:
        #     val = f"{val:.2f}"

        # if val == "0" or val == "":
        #     return ""
        if val == "" or (val == 0 and unit != "人"):
            return ""

        if isinstance(val, float):
            val = algin_float_string(val, dot_bits)

        return f"{comp}(简称{abb})在{year}的{str(keyword)}是{val}{unit}。"
    except Exception as e:
        print("qeury_single_klg_err", e)
    
    return ""

if __name__ == "__main__":
    import sqlite3
    db = sqlite3.connect("test.db")
    cursor = db.cursor()
    print(query_single_klg(cursor, "three_big_tables", "浙江海翔药业股份有限公司", "2019年", "负债合计"))
    print(query_single_klg(cursor, "three_big_tables", "生物股份", "2019年", "负债合计"))