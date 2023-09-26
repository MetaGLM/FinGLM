# pdf_to_txt
这是一个专门为年报文本PDF数据设计的PDF转TXT工具。
这款工具可以快速准确地将PDF文件转换为TXT格式。它能够识别PDF中的文字、表格，并尽可能保持原有的格式。

免责声明：
请注意，虽然我们的PDF转TXT工具已经尽最大努力确保数据转换的准确性和完整性，但由于PDF格式的复杂性以及各种不可预见的因素，可能会在转换过程中产生错误或遗漏。我们强烈建议在使用转换后的TXT数据进行重要决策或报告之前，用户应进行必要的数据核对和验证。
我们的团队对因使用此工具产生的任何直接或间接的损失或责任不承担任何责任。
感谢您的理解和支持，我们将持续改进我们的工具，提供更好的服务。


欢迎大家共同优化这个工具，非常感谢。

另：

extract_table()、find_tables() 是 pdfplumber 中用于从 PDF 中提取表格数据的函数。该函数可以接受一个可选的参数字典，用于更精细地控制表格数据的提取过程。下面介绍一些常用的参数，仅供参考：

vertical_strategy：用于指定垂直方向上的表格线提取策略，可以是 “lines”、“text” 或 “mixed” 中的任意一种，默认值为 “lines”。

horizontal_strategy：用于指定水平方向上的表格线提取策略，可以是 “lines”、“text” 或 “mixed” 中的任意一种，默认值为 “lines”。

snap_tolerance：用于指定在表格提取过程中两个元素之间的距离阈值，如果它们之间的距离小于该值，则会被视为同一元素。默认值为 3。

join_tolerance：用于指定在表格提取过程中两个单元格相连时的距离阈值，如果它们之间的距离小于该值，则它们将被合并为同一个单元格。默认值为 2。

edge_min_length：用于指定在表格提取过程中一个元素的边缘与页面边缘之间的距离阈值，如果它们之间的距离小于该值，则该元素将被忽略。默认值为 10。

min_words：用于指定一个单元格必须包含的最少文本块数目，默认值为 1。

snap_x_tolerance：用于在表格提取过程中校正列位置的参数，允许水平方向上的一些偏离。默认值为 None。

snap_y_tolerance：用于在表格提取过程中校正行位置的参数，允许垂直方向上的一些偏离。默认值为 None。

intersection_x_tolerance：用于调整表格列位置的参数，允许一些列交叉或合并。默认值为 None。

需要注意的是，不同的参数组合可能会产生不同的结果，具体使用时应根据实际情况进行调整。

示例：

    import pdfplumber

    with pdfplumber.open("example.pdf") as pdf:

        first_page = pdf.pages[0]
        
        table_settings = {"intersection_x_tolerance": 1}
        
        table = first_page.extract_table(table_settings)
    
备注：
pdf2txt:新增页眉页脚，重构后的代码。
pdf_to_txt:新增页眉页脚。



