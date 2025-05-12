from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
import os
import pandas as pd
import re

load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")

app = FastAPI()
llm = ChatOpenAI(openai_api_key=openai_api_key, model="gpt-3.5-turbo")

class ChatRequest(BaseModel):
    message: str
    session_id: str

# 전역 대화 세션 저장소
chat_sessions = {}

# 챗봇 응답 API
@app.post("/chat")
def chat(request: ChatRequest):
    try:
        # 프롬프트를 파싱해서 user_context + user_input 나눠서 받을 경우 (또는 app.py에서 둘 다 보내기)
        raw_text = request.message
        context_split = raw_text.split("[질문]")
        if len(context_split) == 2:
            user_context, user_input = context_split
        else:
            user_context = ""
            user_input = raw_text


        # Streamlit 쪽에서 session_id 가져옴
        session_id=request.session_id

        if session_id not in chat_sessions:
            # 첫 메시지: 시스템 지시어 + 컨텍스트
            chat_sessions[session_id] = [
                SystemMessage(content="""당신은 사용자의 금융 상담을 도와주는 AI입니다. 사용자는 지금 이 대화에 직접 참여 중이며, '내', '저', '나' 등은 모두 사용자를 지칭합니다."""),
                HumanMessage(content=user_context.strip())
            ]
        else:
            chat_sessions[session_id].append(HumanMessage(content=f"(참고) {user_context.strip()}"))

        # 사용자 입력 추가
        chat_sessions[session_id].append(HumanMessage(content=user_input.strip()))

        # 응답 생성
        response = llm(chat_sessions[session_id])

        # 응답 메시지도 히스토리에 추가
        chat_sessions[session_id].append(response)

        return {"response": response.content}


    except Exception as e:
        return {"response": f"❌ 오류 발생: {e}"}
