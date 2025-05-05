from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage
import os
import pandas as pd
import re

load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")

app = FastAPI()
llm = ChatOpenAI(openai_api_key=openai_api_key, model="gpt-3.5-turbo")

class ChatRequest(BaseModel):
    message: str

# 고객 ID 추출 함수
def extract_user_id(text: str) -> int | None:
    match = re.search(r'(\d{3})번', text)
    if match:
        return int(match.group(1))
    return None

# 종합 금융 요약 정보 함수
def get_user_profile_summary(user_id: int) -> str:
    try:
        df = pd.read_csv("dummy_users.csv", encoding="cp949")
        user = df[df["user_id"] == user_id]
        if user.empty:
            return f"❌ 고객 ID {user_id}에 해당하는 정보를 찾을 수 없습니다."
        row = user.iloc[0]

        summary = (
            f"📌 {row['name']}님의 금융 요약 정보입니다:\n"
            f"- 나이: {row['age']}세 | 직업: {row['job']} | 연소득: {row['income']:,}원\n"
            f"- 예상 퇴직 나이: {row['expected_retire_age']}세\n\n"
            f"✔ 은행 예금: {row['bank_balance']:,}원 | 대출: {row['loan_balance']:,}원 | 최근 거래일: {row['last_transaction']}\n"
            f"✔ 최근 카드 사용: {row['card_spending']:,}원 ({row['card_category']})\n"
            f"✔ 퇴직연금: {row['pension_balance']:,}원 ({row['pension_type']})\n"
            f"✔ 주식 투자 경험: {'있음' if row['stock_investment']=='Y' else '없음'}\n"
            f"✔ 펀드 투자 경험: {'있음' if row['fund_investment']=='Y' else '없음'}\n"
            f"✔ 가입 보험: {row['insurance_list']} | 월 보험료: {row['insurance_monthly_fee']:,}원"
        )
        return summary
    except Exception as e:
        return f"❌ 고객 정보 조회 중 오류 발생: {e}"

# 챗봇 응답 API
@app.post("/chat")
def chat(request: ChatRequest):
    user_id = extract_user_id(request.message)

    if user_id:
        if "현황" in request.message or "정보" in request.message or "요약" in request.message:
            return {"response": get_user_profile_summary(user_id)}
    

    response = llm([HumanMessage(content=request.message)])
    return {"response": response.content}
