import json
import pandas as pd

# 读取domains.json文件
with open('domains.json', 'r', encoding='utf-8') as file:
    domain_urls = json.load(file)

# 读取domains.xlsx文件，取前三列
excel_data = pd.read_excel('domains.xlsx', usecols=[0, 1, 2], names=['domain', 'div', 'state'])
excel_data = excel_data.fillna("")  # 填充空值

# 遍历 Excel 中的每一行
for index, row in excel_data.iterrows():
    domain = row['domain']
    div = row['div']
    state = row['state']

    # 检查该域名是否存在于 domain_urls 中
    if domain in domain_urls:
        # 如果存在，添加 div 和 state 字段
        domain_urls[domain]['div'] = div if div else ""
        domain_urls[domain]['processed'] = True if state == "已完成" else False
    else:
        # 如果不存在，创建一个新的条目
        domain_urls[domain] = {
            'urls': [],
            'div': div,
            'processed': True if state == "已完成" else False
        }
        print(f"新域名：{domain}")
        
# 将更新后的 domain_urls 保存回 domains.json 文件
with open('domains.json', 'w', encoding='utf-8') as file:
    json.dump(domain_urls, file, ensure_ascii=False, indent=4)
    