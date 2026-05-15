import requests
from bs4 import BeautifulSoup
import re
import os

BASE_URL = "https://tv.9kds.com/"
HEADERS = {"User-Agent": "Mozilla/5.0"}

# 分类规则
GENRE_RULES = {
    "央视": ["CCTV", "央视"],
    "卫视": ["卫视", "东方", "浙江", "江苏", "湖南", "广东", "北京"],
    "地方": ["都市", "新闻", "影视", "少儿", "教育"],
    "港澳台": ["香港", "澳门", "台湾", "翡翠", "明珠", "TVB"],
    "海外": ["韩国", "日本", "马来西亚", "新加坡"]
}

def get_file_links():
    res = requests.get(BASE_URL, headers=HEADERS, timeout=15)
    res.raise_for_status()
    soup = BeautifulSoup(res.text, "html.parser")
    links = []
    for a in soup.find_all("a"):
        href = a.get("href")
        if not href:
            continue
        if href.endswith(".txt") or href.endswith(".m3u"):
            if not href.startswith("http"):
                href = BASE_URL.rstrip("/") + "/" + href.lstrip("/")
            links.append(href)
    return list(set(links))

def parse_m3u_txt(url):
    try:
        text = requests.get(url, headers=HEADERS, timeout=10).text
    except Exception as e:
        print("ERR fetch", url, e)
        return []
    pattern = re.compile(r"([^,#\n]+),(http[s]?://[^\n]+)")
    return pattern.findall(text)

def get_genre(name):
    for genre, keys in GENRE_RULES.items():
        for k in keys:
            if k in name:
                return genre
    return "其他"

def main():
    print("=== 开始抓取 tv.9kds.com ===")
    file_links = get_file_links()
    print("文件数:", len(file_links))

    all_items = []
    for link in file_links:
        items = parse_m3u_txt(link)
        all_items.extend(items)

    # 去重
    seen = set()
    uniq = []
    for n, u in all_items:
        u = u.strip()
        n = n.strip()
        if u and u not in seen:
            seen.add(u)
            uniq.append((n, u))
    print("有效源：", len(uniq))

    # 分组
    groups = {}
    for n, u in uniq:
        g = get_genre(n)
        groups.setdefault(g, []).append((n, u))

    # 输出 txt（标准格式：分组名,#genre#）
    with open("live.txt", "w", encoding="utf-8") as f:
        for g, items in groups.items():
            f.write(f"{g},#genre#\n")  # ✅ 你要的格式
            for n, u in items:
                f.write(f"{n},{u}\n")
            f.write("\n")

    # 输出 m3u（保持不变）
    with open("live.m3u", "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for g, items in groups.items():
            for n, u in items:
                f.write(f'#EXTINF:-1 group-title="{g}",{n}\n{u}\n')

    print("✅ 已生成 live.txt（#genre# 格式）/ live.m3u")

if __name__ == "__main__":
    main()
