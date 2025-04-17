import requests
from bs4 import BeautifulSoup
import json
import os
import time
import re

with open('ref_evluation_all.json', 'r', encoding='utf-8') as file:
    ref_dict = json.load(file)

#"blog.google":"rich-text","trendmicro.com":"richText","crowdstrike.com":"cmp-text","trendmicro.com":"richText","cisa.gov":"l-page-section__content","securelist.com":"js-reading-content","secureworks.com":"article-content"
div_dict = {
    "trendmicro.com": "richText"
}

wrong_urls = []
counts = {"404": 0, "429": 0, "success": 0}

for url in ref_dict.keys():
    for web_dn in div_dict.keys():
        if web_dn in url:
            text_content_all = ""
            if url[-4:].lower() == ".pdf":
                break
            if url in wrong_urls:
                break
            filename = ref_dict[url]["name"] + ".txt"
            
            os.makedirs(f"./documents/{web_dn}/err", exist_ok=True)
            
            error_404 = f"./documents/{web_dn}/err/404_{filename}"
            error_429 = f"./documents/{web_dn}/err/429_{filename}"
            
            error_404_list = []
            error_429_list = []
            
            if os.path.exists(error_404):
                with open(error_404, "r", encoding="utf-8") as file:
                    lines = file.readlines()
                    for line in lines:
                        error_404_list.append(line.strip().split('\t')[0])
            
            if os.path.exists(error_429):
                with open(error_429, "r", encoding="utf-8") as file:
                    lines = file.readlines()
                    for line in lines:
                        error_429_list.append(line.strip().split('\t')[0])

            # 如果已提取好，则跳过，注意需要关注现有文件内容是否正确！
            if os.path.exists(f"./documents/{web_dn}/{filename}"):
                counts["success"] += 1
                break

            # 如果是请求错误或404错误，则跳过提取
            if os.path.exists(error_404) and filename in error_404_list:
                counts["404"] += 1
                break
            


            # print(f"尝试提取：{url} 到 {filename}")
            # ATT&CK中参考文献的网址可能有问题，这里进行修复
            url_match = url.split("https:")
            if len(url_match) > 2 and web_dn in url_match[-1]:
                # 提取到的真实网址
                url = "https:" + url_match[-1]
                print(f"提取到真实链接：{url}")
            if url[:7] == "https:/" and url[7] != "/":
                url = url[:7] + "/" + url[7:]
                print(f"提取到真实链接：{url}")

            try:
                response = requests.get(url)
            except requests.exceptions.RequestException as e:
                print(f"请求错误: {e} 跳过链接：{url}")
                counts["404"] += 1
                # 将404错误信息写入统一的404_error.txt文件
                with open(f"./documents/{web_dn}/err/404_error.txt", "a", encoding="utf-8") as file:
                    file.write(f"{filename}\t{url}\t{e}\n")
                break

            # 检查请求是否成功，如果为429错误，则是请求太多引起的
            if response.status_code != 200:
                print(f"{url} 请求失败，状态码：{response.status_code}")
                if response.status_code == 404:
                    # 尝试是否是末尾/问题：
                    if url[-1] == "/":
                        url = url[:-1]
                    else:
                        url = url + "/"
                    try:
                        response = requests.get(url)
                    except requests.exceptions.RequestException as e2:
                        print(f"请求错误: {e2} 跳过链接：{url}")
                        counts["404"] += 1
                        # 将404错误信息写入统一的404_error.txt文件
                        with open(f"./documents/{web_dn}/err/404_error.txt", "a", encoding="utf-8") as file:
                            file.write(f"{filename}\t{url}\t{e2}\n")
                        break
                    if response.status_code != 200:
                        if response.status_code == 404:
                            counts["404"] += 1
                            # 将404错误信息写入统一的404_error.txt文件
                            with open(f"./documents/{web_dn}/err/404_error.txt", "a", encoding="utf-8") as file:
                                file.write(f"{filename}\t{url}\t{str(response.status_code)}\n")
                        else:
                            counts["429"] += 1
                            # 将429错误信息写入统一的429_error.txt文件
                            with open(f"./documents/{web_dn}/err/429_error.txt", "a", encoding="utf-8") as file:
                                file.write(f"{filename}\t{url}\t{str(response.status_code)}\n")
                        break
                else:
                    counts["429"] += 1
                    # 将429错误信息写入统一的429_error.txt文件
                    with open(f"./documents/{web_dn}/err/429_error.txt", "a", encoding="utf-8") as file:
                        file.write(f"{filename}\t{url}\t{str(response.status_code)}\n")
                    break

            # 解析页面内容
            soup = BeautifulSoup(response.text, 'html.parser')
            rich_text_divs = soup.find_all('div', class_=div_dict[web_dn])
            if rich_text_divs:
                for index, rich_text_div in enumerate(rich_text_divs):
                    # 使用stripped_strings提取所有去掉多余空白的文本
                    text_content = ''.join(rich_text_div.stripped_strings)
                    text_content_all += text_content + "\n"
            else:
                print(f"{url} 没有找到任何指定的div元素!")
                os.makedirs(f"./documents/{web_dn}/err", exist_ok=True)
                counts["429"] += 1
                # 将没有找到指定div元素的错误信息写入429_error.txt文件
                with open(f"./documents/{web_dn}/err/429_error.txt", "a", encoding="utf-8") as file:
                    file.write(f"{filename}\t{url}\t{"没有找到任何指定的div元素!"}\n")
                break

            # 成功提取
            counts["success"] += 1
            os.makedirs(f"./documents/{web_dn}", exist_ok=True)
            with open(f"./documents/{web_dn}/{filename}", "w", encoding="utf-8") as file:
                file.write(text_content_all)
            # 删除错误记录
            if os.path.exists(f"./documents/{web_dn}/err/{filename}"):
                os.remove(f"./documents/{web_dn}/err/{filename}")
            # 成功提取后睡眠10秒
            time.sleep(10)

print(counts)