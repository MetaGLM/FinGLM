import json
import re
import jieba
import time

from .utils import *
from .vector_search import vector_search
from .config import *
from .db.db_schema import schema_fin, schema_base, schema_emp


fin_set = set(schema_fin)
base_set = set(schema_base)
emp_set = set(schema_emp)

base_map = {
    "英文名称": "外文名称",
    "电子邮箱": "电子信箱",
    "互联网地址": "网址"
}
emp_map = {
    "研发人员数量": "研发人员",
    "研究生": "硕士",
    "大学": "本科",
    "大专": "专科",
    "合计": "职工总数"
}
export_fin_table_names = ["合并利润表", "合并资产负债表", "合并现金流量表"]
tables_pattern = re.compile("合并利润表|合并资产负债表|母公司资产负债表|母公司利润表|合并现金流量表|母公司现金流量表|所有者权益变动表")

patterns = [
    re.compile("目录"),
    re.compile("第[一二三四五六七八九十]+[章节]"),
    re.compile("[一二三四五六七八九十]+[、. ]"),
    re.compile("[（(][一二三四五六七八九十]+[)）][、. ]*"),
    re.compile("[1234567890]+[、. ]"),
    re.compile("[(（][1234567890]+[)）][、. ]*")
]

dirty_patterns = [
    re.compile("\d+/\d+"),
    re.compile("年度报告")
]

cell_dirty_patterns = [
    re.compile("[一二三四五六七八九十][、. -][\(（]*[一二三四五六七八九十\d]+[\)）]*"),
    re.compile("注释[:：、 一二三四五六七八九十\d]+")
]

def preprocess_key(cell):
    cell = re.sub("[(（].+[)）][.、 ]{0,1}", "", cell)
    cell = re.sub("[\d一二三四五六七八九十]+[.、 ]", "", cell)
    cell = re.sub("其中：|减：|加：|其中:|减:|加:|：|:", "", cell)
    return cell.strip()

def is_dirty_cell(txt, is_fin_table):
    if txt == "":
        return True
    
    if is_fin_table:
        return not (is_number(txt) and abs(float(strip_comma(txt))) > 99)
    return False

def my_groupby2(iterable):
    feature = "text"
    items = []
    for i in iterable:
        if i["type"] == "excel":
            if feature == "excel":
                items.append(i)
            else:
                yield feature, items
                items = [i]
            feature = "excel"
        else:
            if feature == "excel":
                yield feature, items
                items = [i]
                feature = "text"
            else:
                items.append(i)
    yield feature, items

def judge_table_type(part):
    # 合并资产 负债表等
    if any([("项目" in cell) or ("资产" in cell) or ("附注" in cell) for cell in part[0]]):
        return 0
    if len(set([len(row) for row in part])) == 1:
        return 1
    
    return 0

def join_exccel_data(raw_part, is_fin_table, bs=5):
    try:
        part = [json.loads(i["inside"].replace("'", '"')) for i in raw_part]    
        invalid_row_idxs = [j for j in range(1, len(part) - 1) if all([m == "" for m in part[j]])]
        part = [row for i, row in enumerate(part) if i not in invalid_row_idxs]

        if not part:
            return []

        all_dics = []
        for rows in bs_generator(part, bs=bs):
            dic = {}
            for row in rows:
                row = [preprocess_key(row[0])] + [cell for cell in row[1:] if not is_dirty_cell(cell, is_fin_table)]
                if len(row) >= 2:
                    dic[row[0]] = row[1]
                else:
                    dic[row[0]] = ""
            all_dics.append(json.dumps(dic, ensure_ascii=False))
        return all_dics
    except json.decoder.JSONDecodeError as e:
        return []

class DocTreeNode:
    def __init__(self, content, parent=None, is_leaf=False, type_=-1, is_excel=False):
        # -1: 普通的文本内容
        # 0123分别为四级标题
        self.type_ = type_
        self.is_excel = is_excel
        self.content = content
        self.children = []
        self.parent = parent
        # 传递根路径
        if self.parent != None:
            self.path = self.parent.path
        
    def __str__(self):
        return self.content
        # return re.sub("_\d", "", self.content)

    def get_dep_str(self, hop=1):
        res = str(self)
        ptr = self
        for _ in range(hop):
            if ptr.parent == None:
                return res
            ptr = ptr.parent
            res = str(ptr) + "\n" + res
        return res

    def print_children(self):
        for i, child in enumerate(self.children):
            print(f"#{i}-is_excel:{child.is_excel}", child)

    def get_all_leaves(self, keyword, only_excel_node=True, include_node=True):
        leaves = []
        for child in self.children:
            if child.type_ == -1:
                leaves.append(child)
                continue
            
            if include_node:
                leaves.append(child)

            if keyword in str(child):
                leaves += child.get_all_leaves(keyword, only_excel_node=only_excel_node)
        if only_excel_node:
            leaves = [i for i in leaves if i.is_excel]
        return leaves

    def search_children(self, query):
        res = []
        for child in self.children:
            if child.type_ == -1:
                if len(re.findall("[^\u4e00-\u9fa5]" + query + "[^\u4e00-\u9fa5]", str(child))) > 0:
                    res.append(child)
            else:
                res += child.search_children(query)
        return res

    def vector_search_children(self, query, k=3):
        all_children = self.get_all_leaves("", only_excel_node=False)
        return vector_search(all_children, query, self.path + "-" + str(self), k=k)

class DocTree:
    def __init__(self, txt_path, read_cache=True):
        self.path = txt_path
        self.lines = open(txt_path, encoding="utf-8").read().split("\n")
        self.json_lines = []
        self.json_loads()
        self.mid_nodes = []
        self.leaves = []
        self.root = DocTreeNode("@root", type_=-1)
        self.root.path = self.path
        self.build_tree()

    def json_loads(self):
        for line in self.lines:
            try:
                line = json.loads(line)
                self.json_lines.append(line)
            except Exception as e:
                # print(e)
                # print(line)
                pass
    
    @classmethod
    def find_pattern(cls, text):
        if is_number(text):
            return -2, ""
        
        find = re.findall(tables_pattern, text)
        if len(find) > 0:
            return 6, find[0]

        for j, dpat in enumerate(dirty_patterns):
            find = re.findall(dpat, text)
            if len(find) >= 1:
                return -2, find[0]
        
        for i, pat in enumerate(patterns):
            find = re.findall(pat, text)
            if len(find) == 1 and (text.startswith(find[0]) or (i == 6 and text.endswith(find[0]))):
                
                if (i == 0 and text == find[0]) or i != 0:
                    return i, find[0]
        return -1, ""
    
    def group_leave_nodes(self, leave_lines, is_fin_table):
        all_docs = []
        is_excels = []
        
        for key, part in my_groupby2(leave_lines):
            if not part:
                continue
                
            if key == "excel":
                part_texts = join_exccel_data(part, is_fin_table)
                all_docs += part_texts
                is_excels += [True] * len(part_texts)
            else:
                part_text = "\n".join([i["inside"] for i in part])
                all_docs.append(part_text)
                is_excels.append(False)
        return all_docs, is_excels
        
    def build_tree(self):
        last_parent = self.root
        last_leaves = []
        for line in self.json_lines:
            text = line.get("inside", "")
            text_type = line.get("type", -2)

            if text_type in ("页眉", "页脚") or text == "":
                continue

            # 表格直接加到last_leaves
            if text_type == "excel":
                last_leaves.append(line)
                continue
                
            type_, pat = self.find_pattern(text)
            
            # 过滤的内容
            if type_ == -2:
                continue
                
            if type_ == -1:
                last_leaves.append(line)
            else:
                # 检测到新标题，首先把之前的叶节点内容归档
                if len(last_leaves) > 0:
                    node_texts, is_excels = self.group_leave_nodes(last_leaves, last_parent.type_ == 6)
                    for node_text, is_excel in zip(node_texts, is_excels):
                        new_node = DocTreeNode(node_text, type_=-1, parent=last_parent, is_leaf=True, is_excel=is_excel)
                        last_parent.children.append(new_node)
                        self.leaves.append(new_node)
                    last_leaves = []
                
                # 判断新标题与目前parent层级的关系
                if type_ > last_parent.type_:
                    # 1. 检测出来的层级低于目前层级
                    new_node = DocTreeNode(text, type_=type_, parent=last_parent)
                    last_parent.children.append(new_node)
                    last_parent = new_node
                else:
                    while type_ <= last_parent.type_:
                        last_parent = last_parent.parent
                    new_node = DocTreeNode(text, type_=type_, parent=last_parent)
                    last_parent.children.append(new_node)
                    last_parent = new_node
                self.mid_nodes.append(new_node)

                # for debug
                # print(f"#{type_}#", text)

    def search_leaf(self, query, k=1, only_excel_node=True):
        query_words = query.split(" ")
        nodes = []
        hit_lens = []
        for node in self.leaves:
            if only_excel_node and not node.is_excel:
                continue
            
            nodes.append(node)
            hit_len = 0
            for word in query_words:
                if word in str(node):
                    hit_len += len(word)

            hit_lens.append(hit_len)
        node_hit_zips = [(n, h) for n, h in zip(nodes, hit_lens)]
        sorted_node_hit_zips = sorted(node_hit_zips, key=lambda x: x[1], reverse=True)
        return [i[0] for i in sorted_node_hit_zips[:k] if i[1] > 0]

    def regular_search(self, query, k=1, only_excel_node=True):
        query_words = query.split(" ")
        print("#regular search", query_words)
        nodes = []
        hit_lens = []
        for node in self.leaves:
            if only_excel_node and not node.is_excel:
                continue
            
            nodes.append(node)
            hit_len = 0
            for word in query_words:
                if word in str(node):
                    hit_len += len(word)

            hit_lens.append(hit_len)
        node_hit_zips = [(n, h) for n, h in zip(nodes, hit_lens)]
        sorted_node_hit_zips = sorted(node_hit_zips, key=lambda x: x[1], reverse=True)
        return [str(i[0]) for i in sorted_node_hit_zips[:k] if i[1] > 0]
        
    def search_node(self, query):
        nodes = []
        for node in self.mid_nodes:
            if query in str(node):
                nodes.append(node)
        return nodes

    def vector_search_node(self, query, k=1):
        return vector_search(self.mid_nodes, query, self.path + "-node", k=k)

    def export_fin_tables(self):
        fin_table_dic = {}
        dot_bits = '0'
        for table in export_fin_table_names:
            table_nodes = self.search_node(table)
            if len(table_nodes) == 0:
                # print(f"export fail: {self.path}-{table}")
                continue

            table_dic = {}
            for table_node in table_nodes:
                for child in table_node.children:
                    if not child.is_excel:
                        continue
                    try:
                        dic = json.loads(str(child))
                    except Exception as e:
                        continue
                    for k, v in dic.items():
                        if k == "实收资本": k = "股本"
                        if k in fin_set and k not in table_dic:
                            v = strip_comma(v)
                            if len(v) > 5 and "." in v:
                                dot_bits = str(len(v) - v.find(".") - 1)
                            table_dic[k] = my_float(v)
                            # table_dic[k] = v
                fin_table_dic[table] = table_dic
        fin_table_dic["小数位数"] = dot_bits

        return fin_table_dic

    def export_base_table(self):
        base_re = re.compile("外文名称|英文名称|法定代表人|注册地址|办公地址|电子邮箱|电子信箱|网址|互联网地址")
        base_table_dic = {}
        
        visited_cache = set()
        def export_table_node(node):
            if node in visited_cache:
                return
            visited_cache.add(node)

            if node.is_excel:
                try:
                    dic = json.loads(str(node))
                except Exception as e:
                    return
                for k, v in dic.items():
                    mail_code_pos = k.find("邮政编码")
                    if mail_code_pos >= 0:
                        k = k[:mail_code_pos]
                    find = re.findall(base_re, k)
                    if len(find) > 0:
                        k = base_map.get(find[0], find[0])
                        if k in base_set and k not in base_table_dic:
                            base_table_dic[k] = v
            else:
                lines = str(node).split("\n")
                for line in lines:
                    mail_code_pos = line.find("邮政编码")
                    if mail_code_pos >= 0:
                        line = line[:mail_code_pos]
                    find = re.findall(base_re, line)
                    if len(find) == 0:
                        continue
                    splits = re.split("[:：]", line, 1)
                    # print(splits)
                    if len(splits) != 2:
                        continue
                    k = base_map.get(find[0], find[0])
                    if k in base_set and k not in base_table_dic:
                        base_table_dic[k] = splits[1]
            
            for child in node.children:
                export_table_node(child)

        tables = ["公司简介", "公司情况", "公司基本信息", "公司基本情况"]
        for table in tables:
            table_nodes = self.search_node(table)
            [export_table_node(table_node) for table_node in table_nodes]
                        
        return base_table_dic

    def export_employee_table(self):
        # 研发人员的re
        rs_re = re.compile("研发人员")
        # 员工情况的re
        emp_re = re.compile("研发人员|技术人员|生产人员|销售人员|行政人员|财务人员|小学|初中|高中|专科|本科|硕士|博士|大专|研究生|大学|中专|合计|职工总数")
        emp_table_dic = {}

        visited_cache = set()
        def export_emp(node, pattern):
            if node in visited_cache:
                return
            visited_cache.add(node)

            if node.is_excel:
                try:
                    dic = json.loads(str(node))
                except Exception as e:
                    return
                for k, v in dic.items():
                    # print(k, v, is_int(v))
                    if len(re.findall("研发投入|比例|比重|报酬|薪资", k)) > 0 or not is_int(v):
                        continue 
                    find = re.findall(pattern, k)
                    if len(find) > 0:
                        # print(k, v)
                        k = emp_map.get(find[0], find[0])
                        if k in emp_set and k not in emp_table_dic:
                            v = strip_comma(v)
                            emp_table_dic[k] = my_int(v)
                            # emp_table_dic[k] = v
            for child in node.children:
                export_emp(child, pattern)
        
        # 找研发人数
        rs_table_nodes = self.search_node("研发投入")
        [export_emp(table_node, rs_re) for table_node in rs_table_nodes[::-1]]

        tables = ["员工数量", "员工情况"]
        for table in tables:
            table_nodes = self.search_node(table)
            [export_emp(table_node, emp_re) for table_node in table_nodes[::-1]]

        return emp_table_dic

def check_export_stats():
    fin_cnt = 0
    base_cnt = 0
    emp_cnt = 0
    i = 0

    for name in tqdm(open(PDF_IDX_PATH)):
        if not name.strip():
            continue
        name = name.strip()
        i += 1
        path = get_txt_path(name)
        if not os.path.exists(path):
            continue 
        dt = DocTree(path)

        fin = dt.export_fin_tables()
        base = dt.export_base_table()
        emp = dt.export_employee_table()

        fin_cnt += len(fin)
        base_cnt += len(base)
        emp_cnt += len(emp)

    print("fin", fin_cnt / (len(schema_fin) * i), fin_cnt)
    print("base", base_cnt / (len(schema_base) * i), base_cnt)
    print("emp", emp_cnt / (len(schema_emp) * i), emp_cnt)


if __name__ == "__main__":
    # s = time.time()
    dt = DocTree(get_txt_path("2022-03-16__广东迪生力汽配股份有限公司__603335__迪生力__2021年__年度报告.txt"))
    from pprint import pprint
    pprint(dt.export_fin_tables())
    # print("time_cost: ", time.time() - s)
    # dt.search_node("合并利润表")[0].print_children()


    # TODO 导出股份总数