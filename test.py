import json
import pandas as pd

# 读取domains.json文件
with open('domains.json', 'r', encoding='utf-8') as file:
    domain_urls = json.load(file)

# 读取domains.xlsx文件，取相关列
excel_data = pd.read_excel('domains.xlsx', header=[0, 1])

# 遍历 Excel 中的每一行
for index, row in excel_data.iterrows():
    domain = row[('domain', '')]
    div_list = []
    for div_key in [('div', 'div1'), ('div', 'div2'), ('div', 'div3')]:
        div = row[div_key]
        if pd.notnull(div):
            div_list.append(div)
    state = row[('state', '')]

    # 检查该域名是否存在于 domain_urls 中
    if domain in domain_urls:
        # 如果存在，添加 div 和 state 字段
        domain_urls[domain]['div'] = div_list
        if state == "已完成":
            domain_urls[domain]['processed'] = True
        elif state == "问题":
            domain_urls[domain]['processed'] = None
        else:
            domain_urls[domain]['processed'] = False
    else:
        # 如果不存在，创建一个新的条目
        domain_urls[domain] = {
            'urls': [],
            'div': div_list,
            'processed': True if state == "已完成" else False
        }
        print(f"新域名：{domain}")

# 将更新后的 domain_urls 保存回 domains.json 文件
with open('domains.json', 'w', encoding='utf-8') as file:
    json.dump(domain_urls, file, ensure_ascii=False, indent=4)