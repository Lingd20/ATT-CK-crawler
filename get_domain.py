import os
import json
from openpyxl import Workbook

# 读取JSON文件
with open('ref_evluation_all.json', 'r', encoding='utf-8') as file:
    ref_dict = json.load(file)

# 存储每个域名对应的URL列表
domain_urls = {}
for url in ref_dict.keys():
    original_url = url
    if url.startswith("http://"):
        url = url[7:]
    if url.startswith("https://"):
        url = url[8:]
    if url.startswith("www."):
        url = url[4:]

    domain = url.split("/")[0]
    if domain not in domain_urls:
        domain_urls[domain] = {'urls': []}
    domain_urls[domain]['urls'].append(original_url)
import os
import json
from openpyxl import Workbook


def merge_domains(domain_urls, new_domain, url):
    for existing_domain in list(domain_urls.keys()):
        if existing_domain in new_domain:
            # 已有域名是新域名的子串，将新域名合并到已有域名下
            domain_urls[existing_domain]['urls'].append(url)
            return domain_urls
        elif new_domain in existing_domain:
            # 新域名是已有域名的子串，用新域名替换已有域名
            domain_urls[new_domain] = domain_urls.pop(existing_domain)
            domain_urls[new_domain]['urls'].append(url)
            return domain_urls
    # 新域名与已有域名无包含关系，添加新域名
    domain_urls[new_domain] = {'urls': [url]}
    return domain_urls


# 读取JSON文件
with open('ref_evluation_all.json', 'r', encoding='utf-8') as file:
    ref_dict = json.load(file)

# 存储每个域名对应的URL列表
domain_urls = {}
for url in ref_dict.keys():
    if url[-4:].lower() == ".pdf":
        continue
    original_url = url
    if url.startswith("http://"):
        url = url[7:]
    if url.startswith("https://"):
        url = url[8:]
    if url.startswith("www."):
        url = url[4:]

    domain = url.split("/")[0]
    domain_urls = merge_domains(domain_urls, domain, original_url)

# 保存为JSON文件
with open('domains_new.json', 'w', encoding='utf-8') as file:
    json.dump(domain_urls, file, ensure_ascii=False, indent=4)

# 创建一个新的工作簿
wb = Workbook()
ws = wb.active
# 设置表头
ws.append(['domain', 'url_example'])

# 遍历每个域名，将域名和对应的一个URL示例写入XLSX文件
for domain, data in domain_urls.items():
    url_example = data['urls'][0] if data['urls'] else ''
    ws.append([domain, url_example])

# 保存为XLSX文件
wb.save('domains.xlsx')
    
# 保存为JSON文件
with open('domains.json', 'w', encoding='utf-8') as file:
    json.dump(domain_urls, file, ensure_ascii=False, indent=4)

# 创建一个新的工作簿
wb = Workbook()
ws = wb.active
# 设置表头
ws.append(['domain', 'url_example'])

# 遍历每个域名，将域名和对应的一个URL示例写入XLSX文件
for domain, data in domain_urls.items():
    url_example = data['urls'][0] if data['urls'] else ''
    ws.append([domain, url_example])

# 保存为XLSX文件
wb.save('domains.xlsx')
    