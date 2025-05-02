import streamlit as st
import requests

st.title("🤖 LangChain Chatbot (FastAPI 연동)")

if "chat_log" not in st.session_state:
    st.session_state.chat_log = []

user_input = st.text_input("You:", key="input")

if user_input:
    # FastAPI 서버로 메시지 POST
    try:
        response = requests.post(
            "http://localhost:8000/chat",
            json={"message": user_input},
            timeout=10
        )
        response.raise_for_status()
        bot_reply = response.json()["response"]
    except Exception as e:
        bot_reply = f"❌ 에러 발생: {e}"

    # 대화 저장
    st.session_state.chat_log.append(("You", user_input))
    st.session_state.chat_log.append(("Bot", bot_reply))

# 대화 히스토리 출력
for speaker, msg in st.session_state.chat_log:
    st.markdown(f"**{speaker}:** {msg}")