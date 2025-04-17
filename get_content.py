import requests
from bs4 import BeautifulSoup
import json
import os
import time
import re
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='crawler.log',
    filemode='a',  # Append mode
    encoding='utf-8',
)

def save_error_info(error_file, name2info):
    with open(error_file, 'w', encoding='utf-8') as file:
        json.dump(name2info, file, ensure_ascii=False, indent=4)


def load_error_info(error_file):
    if not os.path.exists(error_file):
        return {}, []
    with open(error_file, 'r', encoding='utf-8') as file:
        try:
            name2info = json.load(file)
            name_list = list(name2info.keys())
            return name2info, name_list
        except json.JSONDecodeError:
            return {}, []

def sanitize_filename(filename, log_file_path, web_dn=None):
    illegal_chars = r'[\\/*?:"<>|]'
    if re.search(illegal_chars, filename):
        sanitized = re.sub(illegal_chars, '_', filename)
        with open(log_file_path, 'a', encoding='utf-8') as log_file:
            log_file.write(f"域名：{web_dn}\t原始文件名: {filename}\t实际文件名: {sanitized}\n")
        return sanitized
    else:
        return filename



with open('ref_evluation_all.json', 'r', encoding='utf-8') as file:
    ref_dict = json.load(file)

# div_dict = {
#     "trendmicro.com": "richText",
#     "blog.google":"rich-text",
#     "crowdstrike.com":"cmp-text",
#     "cisa.gov":"l-page-section__content",
#     "securelist.com":"js-reading-content",
#     "secureworks.com":"article-content"
# }
div_dict = {}
with open('domains.json', 'r', encoding='utf-8') as file:
    domain_urls = json.load(file)
    for domain in domain_urls.keys():
        if domain_urls[domain]["div"] != "" and domain_urls[domain]["processed"] == False:
            div_dict[domain] = domain_urls[domain]["div"]

print(f"本次提取的域名数量：{len(div_dict)}")
print(div_dict)

wrong_urls = []


headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
    "Accept-Language": "en-US,en;q=0.9"
}


for web_dn in div_dict.keys():
    counts = {"404": 0, "429": 0, "success": 0}
    
    os.makedirs(f"./documents/{web_dn}/err", exist_ok=True)
    
    error_404 = f"./documents/{web_dn}/err/404_error.txt"
    error_429 = f"./documents/{web_dn}/err/429_error.txt"
    success_dir = f"./documents/{web_dn}/success"
    os.makedirs(success_dir, exist_ok=True)
    
    error_404_name2info, error_404_list = load_error_info(error_404)
    error_429_name2info, error_429_list = load_error_info(error_429)

    filename_log = f"./documents/file_name_log.txt"

    for url in ref_dict.keys():
        if web_dn in url:
            text_content_all = ""
            if url[-4:].lower() == ".pdf":
                continue
            if url in wrong_urls:
                continue
            filename = ref_dict[url]["name"] + ".txt"


            # 如果已提取好，则跳过，注意需要关注现有文件内容是否正确！
            if os.path.exists(f"./documents/{web_dn}/{filename}"):
                counts["success"] += 1
                continue

            # 如果是请求错误或404错误，则跳过提取
            if os.path.exists(error_404) and filename in error_404_list:
                counts["404"] += 1
                continue
            


            # print(f"尝试提取：{url} 到 {filename}")
            # ATT&CK中参考文献的网址可能有问题，这里进行修复
            url_match = url.split("https:")
            if len(url_match) > 2 and web_dn in url_match[-1]:
                # 提取到的真实网址
                url = "https:" + url_match[-1]
                # print(f"提取到真实链接：{url}")
                logging.info(f"提取到真实链接：{url}")
            if url[:7] == "https:/" and url[7] != "/":
                url = url[:7] + "/" + url[7:]
                # print(f"提取到真实链接：{url}")
                logging.info(f"提取到真实链接：{url}")

            try:
                response = requests.get(url, headers=headers, timeout=30)
            except requests.exceptions.RequestException as e:
                # print(f"请求错误: {e} 跳过链接：{url}")
                logging.info(f"请求错误: {e} 跳过链接：{url}")
                counts["404"] += 1
                
                error_404_list.append(filename)
                error_404_name2info[filename] = [url, str(e)]
                continue

            # 检查请求是否成功，如果为429错误，则是请求太多引起的
            if response.status_code != 200:
                # print(f"{url} 请求失败，状态码：{response.status_code}")
                logging.info(f"{url} 请求失败，状态码：{response.status_code}")
                if response.status_code == 404:
                    # 尝试是否是末尾/问题：
                    if url[-1] == "/":
                        url = url[:-1]
                    else:
                        url = url + "/"
                    try:
                        response = requests.get(url)
                    except requests.exceptions.RequestException as e2:
                        # print(f"请求错误: {e2} 跳过链接：{url}")
                        logging.info(f"请求错误: {e2} 跳过链接：{url}")
                        counts["404"] += 1
                        error_404_list.append(filename)
                        error_404_name2info[filename] = [url, str(e2)]
                        continue
                    if response.status_code != 200:
                        if response.status_code == 404:
                            counts["404"] += 1
                            error_404_list.append(filename)
                            error_404_name2info[filename] = [url, str(response.status_code)]
                        else:
                            counts["429"] += 1
                            if filename not in error_429_list:
                                error_429_list.append(filename)
                            error_429_name2info[filename] = [url, str(response.status_code)]
                        continue
                else:
                    counts["429"] += 1
                    if filename not in error_429_list:
                        error_429_list.append(filename)
                    error_429_name2info[filename] = [url, str(response.status_code)]
                    continue

            # 解析页面内容
            soup = BeautifulSoup(response.text, 'html.parser')
            rich_text_divs = soup.find_all('div', class_=div_dict[web_dn])
            if rich_text_divs:
                for index, rich_text_div in enumerate(rich_text_divs):
                    # 使用stripped_strings提取所有去掉多余空白的文本
                    text_content = ''.join(rich_text_div.stripped_strings)
                    text_content_all += text_content + "\n"
            else:
                # print(f"{url} 没有找到任何指定的div元素!")
                logging.info(f"{url} 没有找到任何指定的div元素!")
                counts["429"] += 1
                if filename not in error_429_list:
                    error_429_list.append(filename)
                error_429_name2info[filename] = [url, "没有找到任何指定的div元素!"]
                continue

            # 成功提取
            counts["success"] += 1
            filename = sanitize_filename(filename, filename_log, web_dn)

            with open(f"{success_dir}/{filename}", "w", encoding="utf-8") as file:
                file.write(text_content_all)
            logging.info(f"成功提取：{url} 到 {filename}")
            # 删除错误记录
            if filename in error_404_list:
                error_404_list.remove(filename)
            if filename in error_429_list:
                error_429_list.remove(filename)
                
            # 成功提取后睡眠10秒
            time.sleep(10)
    # 写入错误记录
    save_error_info(error_404, error_404_name2info)
    save_error_info(error_429, error_429_name2info)
            
    print(f"{web_dn}: {counts}")
    logging.info(f"{web_dn}: {counts}")