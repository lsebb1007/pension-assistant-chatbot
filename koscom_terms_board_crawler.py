import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime

BASE_URL = "https://www.koscom.co.kr"
LIST_URL = BASE_URL + "/portal/bbs/B0000034/list.do?isk={isk}&menuNo=200646&pageIndex={page}"

CHOSUNG_MAP = {
    'ㄱ': 1, 'ㄴ': 2, 'ㄷ': 3, 'ㄹ': 4, 'ㅁ': 5, 'ㅂ': 6, 'ㅅ': 7, 'ㅇ': 8, 
    'ㅈ': 9, 'ㅊ': 10, 'ㅋ': 11, 'ㅌ': 12, 'ㅍ': 13, 'ㅎ': 14
}

def parse_term_ul(ul):
    dl = ul.find('dl', class_='type1')
    if not dl:
        return None
    dt = dl.find('dt')
    if not dt:
        return None
    term = dt.find('strong').get_text(strip=True)
    # 대표설명: 첫 번째 .con_hid.on, 상세설명: 두 번째 .con_hid
    brief_desc = dl.find('p', class_='con_hid on')
    full_desc = dl.find_all('p', class_='con_hid')
    full_desc = full_desc[1].get_text(strip=True) if len(full_desc) > 1 else ''
    return {
        'term': term,
        'brief': brief_desc.get_text(strip=True) if brief_desc else '',
        'desc': full_desc
    }

def crawl_koscom_terms_board(save_dir='docs', filename='koscom_terms_board.md'):
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    save_path = os.path.join(save_dir, filename)
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    with open(save_path, "w", encoding="utf-8") as f:
        f.write(f"# 코스콤 금융IT 용어사전 (초성별 전체/페이지별 크롤링, {now})\n\n")
        f.write(f"출처: {BASE_URL}/portal/bbs/B0000034/list.do?menuNo=200646\n\n---\n\n")
    
    for chosung, isk in CHOSUNG_MAP.items():
        print(f"[{chosung}] 크롤링중...")
        page = 1
        total_terms = 0
        while True:
            url = LIST_URL.format(isk=isk, page=page)
            resp = requests.get(url)
            soup = BeautifulSoup(resp.text, "html.parser")
            ul_list = soup.select("div.bbs_photo1 > ul")
            if not ul_list:
                break
            terms = []
            for ul in ul_list:
                parsed = parse_term_ul(ul)
                if parsed:
                    terms.append(parsed)
            if not terms:
                break
            with open(save_path, "a", encoding="utf-8") as f:
                if page == 1:
                    f.write(f"## {chosung} 초성\n\n")
                for t in terms:
                    f.write(f"### {t['term']}\n")
                    f.write(f"- 간략설명: {t['brief']}\n\n")
                    f.write(f"{t['desc']}\n\n")
                f.write("\n")
            print(f"  - {page}페이지, {len(terms)}건")
            total_terms += len(terms)
            # 다음 페이지 링크가 없으면 종료
            next_link = soup.select_one("div.paging ol li a[title='다음 페이지']")
            if not next_link and len(terms) < 10:
                break
            page += 1
        print(f"  ▶ {total_terms}개 용어 수집 완료")
        with open(save_path, "a", encoding="utf-8") as f:
            f.write("---\n\n")
    print(f"\n크롤링 완료! → {save_path}")

if __name__ == "__main__":
    crawl_koscom_terms_board()
