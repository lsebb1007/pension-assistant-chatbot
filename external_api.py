import requests
import pandas as pd
import os
from datetime import datetime
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

import requests
from bs4 import BeautifulSoup
import os

# 환경변수 또는 직접 대입
API_KEY = os.getenv("LAW_API_KEY") # 예시: g4c@korea.kr → "g4c"

def get_law_id_and_mst(law_name: str) -> tuple[str, str]:
    """법령명으로 검색하여 (법령ID, MST번호) 추출"""
    url = "http://www.law.go.kr/DRF/lawSearch.do"
    params = {
        "OC": API_KEY,
        "target": "law",
        "type": "XML",
        "query": law_name,
        "display": 1
    }

    res = requests.get(url, params=params)
    res.raise_for_status()
    soup = BeautifulSoup(res.content, "lxml-xml")
    law_id = soup.find("법령ID")
    mst = soup.find("법령일련번호")  # lawService.do?MST= 에 사용
    if not law_id or not mst:
        raise ValueError("❌ 해당 법령명을 찾을 수 없습니다.")
    return law_id.text.strip(), mst.text.strip()


def get_law_full_text(mst: str) -> str:
    """MST로 전체 본문을 XML로 받아 텍스트로 변환"""
    url = "http://www.law.go.kr/DRF/lawService.do"
    params = {
        "OC": API_KEY,
        "target": "law",
        "type": "XML",
        "MST": mst
    }

    res = requests.get(url, params=params)
    res.raise_for_status()
    soup = BeautifulSoup(res.content, "xml")
    return soup.get_text(separator="\n").strip()


def save_law_text_by_name(law_name: str, save_path: str):
    """법령명으로 전체 전문 저장"""
    try:
        print(f"🔍 '{law_name}' 검색 중...")
        law_id, mst = get_law_id_and_mst(law_name)
        print(f"✅ 법령ID: {law_id}, MST: {mst}")

        print("📥 본문 가져오는 중...")
        full_text = get_law_full_text(mst)

        with open(save_path, "w", encoding="utf-8") as f:
            f.write(full_text)
        print(f"📄 저장 완료: {save_path}")

    except Exception as e:
        print(f"❌ 오류 발생: {e}")

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

# 법 전문 다운로드
if __name__ == "__main__":
    # 퇴직연금 관련 법령 리스트
    retirement_laws = [
        "근로자퇴직급여보장법",
        "국민연금법",
    ]

    for law_name in retirement_laws:
        filename = f"{law_name}_전문.txt"
        try:
            save_law_text_by_name(law_name, filename)
        except Exception as e:
            print(f"❌ {law_name} 처리 중 오류 발생: {e}")
