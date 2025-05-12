import requests
import pandas as pd
import os
from datetime import datetime
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

CORP_NAME_ALIAS = {
    "삼성전자": "삼성전자㈜",
    "현대차": "현대자동차",
    "카카오": "㈜카카오",
    "네이버": "네이버(주)",
    # 필요시 확장
}

def fetch_law_detail(law_name, oc_id="g4c"):
    base_url = "http://www.law.go.kr/DRF/lawSearch.do"
    params = {
        "OC": "rhxodud9709",
        "target": "law",
        "type": "HTML",
        "query": law_name,
        "search": 1
    }

    try:
        search_res = requests.get(base_url, params=params, timeout=5)
        search_res.raise_for_status()
        soup = BeautifulSoup(search_res.text, "html.parser")
        first_result = soup.select_one("table tbody tr td a")
        if not first_result:
            return {"summary": "❌ 해당 법령을 찾을 수 없습니다."}
        
        law_link = "http://www.law.go.kr" + first_result["href"]
        law_detail = requests.get(law_link, timeout=5)
        law_detail.raise_for_status()
        soup_detail = BeautifulSoup(law_detail.text, "html.parser")
        content = soup_detail.get_text()
        summary = content.strip()[:1000] + "..."  # 요약 처리
        return {"summary": summary}
    except Exception as e:
        return {"summary": f"❌ 오류 발생: {e}"}


def fetch_dart_summary(corp_name):
    df = pd.read_csv("corp_list.csv")
    df["corp_code"] = df["corp_code"].astype(str).str.zfill(8)  # ← 핵심!
    df["corp_name_clean"] = df["corp_name"].astype(str).str.replace("㈜", "").str.strip().str.lower()
    search_name = corp_name.strip().lower()

    # 1️⃣ 완전일치 우선
    exact_match = df[df["corp_name_clean"] == search_name]
    if not exact_match.empty:
        corp_code = exact_match.iloc[0]["corp_code"]
    else:
        # 2️⃣ 포함 검색 fallback
        partial_match = df[df["corp_name_clean"].str.contains(search_name)]
        if partial_match.empty:
            return {"summary": f"❌ '{corp_name}'에 대한 기업 코드를 찾을 수 없습니다."}
        corp_code = partial_match.iloc[0]["corp_code"]

    api_key = os.getenv("DART_API_KEY")
    today = datetime.today().strftime("%Y%m%d")

    params = {
        "crtfc_key": api_key,
        "corp_code": corp_code,
        "bgn_de": "20240101",
        "end_de": today,
        "page_count": 5
    }

    print("[DEBUG] 요청 파라미터:", params)

    try:
        res = requests.get("https://opendart.fss.or.kr/api/list.json", params=params)
        print("[DEBUG] 응답 상태코드:", res.status_code)
        print("[DEBUG] 응답 본문 (앞 300자):", res.text[:300])
        data = res.json()
    except Exception as e:
        return {"summary": f"❌ 요청 또는 JSON 파싱 오류: {e}"}

    report_list = data.get("list", [])
    if not report_list:
        return {"summary": f"{corp_name}에 대한 최근 공시가 없습니다."}

    summary = "\n".join([f"- {r['report_nm']} ({r['rcept_dt']})" for r in report_list])
    return {"summary": f"{corp_name}의 최근 공시 목록:\n{summary}"}
