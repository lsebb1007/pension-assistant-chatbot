from fastapi.middleware.cors import CORSMiddleware
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from fastapi import FastAPI, Query
from pydantic import BaseModel
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
import os
import pandas as pd
import re
from external_api import fetch_law_detail, fetch_dart_summary

load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 개발 중엔 전체 허용, 실제 운영시엔 보안 강화 필요
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

llm = ChatOpenAI(openai_api_key=openai_api_key, model="gpt-3.5-turbo")

# faiss_index 벡터DB 로드 (최초 1회만)
embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)
vectorstore = FAISS.load_local(
    "faiss_index", embeddings,
    allow_dangerous_deserialization=True
)

def toint(x):
    try:
        return int(float(str(x).replace(",", "").strip()))
    except Exception:
        return 0

def get_customer_summary():
    df = pd.read_csv("customer_summary.csv", encoding="utf-8")
    d = df.iloc[0].to_dict()
    summary = (
        f"이름: {d['name']}, 나이: {d['age']}, 직업: {d['job']}\n"
        f"연소득: {toint(d['income']):,}원, 은행잔고: {toint(d['bank_balance']):,}원, 대출잔고: {toint(d['loan_balance']):,}원\n"
        f"최근거래일: {d['last_transaction']}, 카드소비: {toint(d['card_spending']):,}원, 소비카테고리: {d['card_category']}\n"
        f"퇴직연금 유형: {d['pension_type']}, 잔고: {toint(d['pension_balance']):,}원\n"
        f"주식투자여부: {d['stock_investment']}, 펀드투자여부: {d['fund_investment']}\n"
        f"보험: {d['insurance_list']}, 월 보험료: {toint(d['insurance_monthly_fee']):,}원\n"
        f"보유 ETF: {d['owned_etf']}\n"
    )
    return summary


class ChatRequest(BaseModel):
    message: str
    session_id: str

# 전역 대화 세션 저장소
chat_sessions = {}

# 챗봇 응답 API
@app.post("/chat")
def chat(request: ChatRequest):
    try:
        raw_text = request.message

        # 고객요약정보 항상 삽입
        customer_info = get_customer_summary()
        user_context = f"[고객 요약정보]\n{customer_info}"

        context_split = raw_text.split("[질문]")
        if len(context_split) == 2:
            extra_context, user_input = context_split
            user_context += "\n" + extra_context
        else:
            user_input = raw_text

        session_id = request.session_id

        # 💡 벡터DB에서 유사 근거 검색
        docs_and_scores = vectorstore.similarity_search_with_score(user_input, k=3)
        retrieved_context = "\n---\n".join([doc.page_content for doc, score in docs_and_scores])

        # 💡 최종 프롬프트 확장
        final_prompt = f"""{user_context.strip()}

[근거]
{retrieved_context}

[질문]
{user_input.strip()}
        """

        # 히스토리 관리
        if session_id not in chat_sessions:
            chat_sessions[session_id] = [
                SystemMessage(content="""당신은 사용자의 금융 상담을 도와주는 AI입니다. '내', '저', '나' 등은 모두 사용자를 지칭합니다. 반드시 [근거] 내에서만 답변하세요."""),
                HumanMessage(content=final_prompt)
            ]
        else:
            chat_sessions[session_id].append(HumanMessage(content=f"(참고) {final_prompt}"))

        chat_sessions[session_id].append(HumanMessage(content=user_input.strip()))
        response = llm(chat_sessions[session_id])
        chat_sessions[session_id].append(response)

        return {"response": response.content}

    except Exception as e:
        return {"response": f"❌ 오류 발생: {e}"}


@app.post("/fetch-law-detail")
def law_search(law_name: str = Query(...)):
    return fetch_law_detail(law_name)


@app.post("/fetch-dart-summary")
def dart_summary(corp_name: str = Query(...)):
    print(f"[📥 DART 요청] corp_name: {corp_name}")
    result = fetch_dart_summary(corp_name)
    print(f"[📤 DART 응답] {result}")
    return result