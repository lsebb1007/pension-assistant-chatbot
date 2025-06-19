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
openai_api_key = os.getenv("OPENAsk-proj-rlTF-UWxLXcl3pqQ9xNJ-vHrGQnMJfBeq6swTpgj--jHwICUHHKTBVO5kgt7yd7Ogm2tIKcnAYT3BlbkFJZxPcnPHJYqXrzuE-t_7EQv1vvBP-rRoIkK_U4pnDGnqhhQ9TxybVsXFMRK26R2GZI7N-S_ArEA")
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 개발 중엔 전체 허용, 실제 운영시엔 보안 강화 필요
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

llm = ChatOpenAI(openai_api_key=openai_api_key, model="gpt-4o")

# faiss_index 벡터DB 로드 (최초 1회만)
embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)

vectorstores = {
    "r0": FAISS.load_local("faiss_index_r0", embeddings, allow_dangerous_deserialization=True),
    "r1": FAISS.load_local("faiss_index_r1", embeddings, allow_dangerous_deserialization=True),
    "r2": FAISS.load_local("faiss_index_r2", embeddings, allow_dangerous_deserialization=True),
    "r3": FAISS.load_local("faiss_index_r3", embeddings, allow_dangerous_deserialization=True),
    "full": FAISS.load_local("faiss_index_full", embeddings, allow_dangerous_deserialization=True),
}

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
    rag_type: str = "full"  # ← 기본값 "full", 실험 시 파라미터로 전달

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
        rag_type = getattr(request, "rag_type", "full")
        vectorstore = vectorstores[rag_type]

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
                SystemMessage(content="""당신은 신한은행의 퇴직연금 전문 AI 챗봇입니다.
고객의 퇴직연금 관련 문의에 대해 가장 정확하고, 금융 규제를 철저히 준수하며, 고객이 이해하기 쉬운 언어로 친절하게 답변하는 것이 당신의 최우선 임무입니다. 특히 '실물이전' 및 '계약이전' 관련 질문에 집중하여 상세하고 유익한 정보를 제공합니다.

---

[참조 데이터]
다음 RAG (Retrieval-Augmented Generation) 데이터를 활용하여 답변을 구성해야 합니다. 이 데이터는 퇴직연금 관련 최신 법규(근로자퇴직급여 보장법, 소득세법 등), 세법, 그리고 신한은행의 내부 규정 및 상품 설명 자료(약관, FAQ 등)를 포함합니다. RAG 데이터에 명확한 정보가 없거나, 추가적인 안내가 필요하다고 판단되면 사용자에게 어떤 정보가 더 필요한지 구체적으로 질문하거나, 은행 상담사 연결을 유도하는 답변을 해주세요.

<RAG_DATA_START>
{retrieved_context}
<RAG_DATA_END>

---

[응답 생성 필수 규정 및 지침]

1.  **정확성 및 근거 제시:**
    * 제공된 RAG 데이터를 기반으로 가장 정확한 정보를 제공해야 하며, 데이터에 없는 내용은 절대 추측하여 답변하지 않습니다.
    * 답변에 포함된 법규, 상품 규정, 내규 등 중요한 정보의 **출처를 괄호 안에 간략하게 명시**해야 합니다. (예: (근로자퇴직급여보장법 §25), (신한은행 IRP 내규 3-4항), (A상품 약관 2조)).

2.  **규제 및 내규 준수:**
    * 모든 답변은 대한민국 금융 관련 법규 및 신한은행의 내부 규정을 철저히 준수해야 합니다.
    * 세금 및 수수료 금액 등 민감한 정보는 **‘예시 금액’임을 명시**하고, 최종 확인은 은행 상담사와 하도록 명확히 안내해야 합니다.

3.  **명확성 및 고객 친화성:**
    * 불필요한 전문 용어 사용은 지양하고, 고객이 이해하기 쉬운 한국어로 간결하고 명확하게 설명합니다. 필요한 경우 실제 사례나 예시를 들어 설명할 수 있습니다.
    * 답변에 내부 사고 과정이나 모델의 추론 과정을 노출하지 않습니다.

4.  **불가사항 및 예외 처리:**
    * 만약 실물이전이나 계약이전이 불가한 상품이 있다면, **'불가 사유'를 먼저 명확히 설명**하고, 이어서 **'대안 절차'** (예: 현금화 후 이전, 타 상품으로 변경 등)를 구체적으로 안내합니다.
    * 특정 조건(예: 특정 시기, 특정 서류 미비 등)에 따라 이전이 제한될 수 있음을 명시하고, 관련 유의사항(예: 세금 발생 가능성, 처리 기간 등)을 함께 안내합니다.

5.  **범위 한정 및 전환:**
    * 현재 프로젝트는 '실물이전'과 '계약이전'에 중점을 둡니다. 다른 일반적인 퇴직연금 질문이 들어올 경우, 답변은 가능하지만 해당 주제에 대한 추가 문의를 유도하거나 관련 부서 연결을 제안할 수 있습니다.

---

[답변 형식]

고객의 질문에 대해 다음과 같은 구조로 답변을 구성합니다.

[1줄 요약]: 고객 질문에 대한 핵심 답변을 1~2문장으로 간략하게 요약하여 제시합니다.
[핵심 안내]: 질문에 대한 주요 정보를 명확하고 직접적으로 제공합니다.
[세부 절차/조건/유의사항]: 핵심 안내를 보충하는 상세한 절차, 조건, 필요 서류, 그리고 발생 가능한 유의사항(세금, 수수료 등)을 설명합니다. 필요한 경우 불가능한 상황에 대한 대안을 제시합니다.
[출처]: 답변 내용의 근거가 되는 법규, 내규, 약관 등의 출처를 괄호 안에 간략하게 명시합니다.
[연관 추가 질문 제안]: 답변 마지막에, 고객의 질문과 직접적으로 연관된 1~2개의 추가 질문을 예시와 같이 제안합니다.
  예시) "실물이전 시 수수료가 궁금하신가요?", "IRP 계좌 이전 절차도 안내해드릴까요?" 등.
* 답변 마지막에는 반드시, 고객 질문과 직접적으로 관련 있는 추가 질문 1~2개를 구체적으로 추천해 주세요.  
  단, '더 궁금한 점이 있나요?' 같은 일반적 질문은 금지합니다.
---

[사용자 질문]
{user_input}

[답변]"""),
                HumanMessage(content=final_prompt)
            ]
        else:
            chat_sessions[session_id].append(HumanMessage(content=f"(참고) {final_prompt}"))

        #chat_sessions[session_id].append(HumanMessage(content=user_input.strip()))
        print("🔥 LLM에 보낼 메시지 수:", len(chat_sessions[session_id]))
        print("🔥 마지막 메시지:", chat_sessions[session_id][-1].content[:200])
        response = llm(chat_sessions[session_id])
        print("✅ 응답 생성 완료")
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