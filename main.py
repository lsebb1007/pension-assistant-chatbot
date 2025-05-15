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
llm = ChatOpenAI(openai_api_key=openai_api_key, model="gpt-3.5-turbo")

# faiss_index 벡터DB 로드 (최초 1회만)
embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)
vectorstore = FAISS.load_local(
    "faiss_index", embeddings,
    allow_dangerous_deserialization=True
)



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
        context_split = raw_text.split("[질문]")
        if len(context_split) == 2:
            user_context, user_input = context_split
        else:
            user_context = ""
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