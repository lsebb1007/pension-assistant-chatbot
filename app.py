import streamlit as st
import pandas as pd
import requests

# 고객 정보 불러오기
@st.cache_data
def load_user_data():
    return pd.read_csv("dummy_users.csv", encoding="utf-8")

df = load_user_data()

# 사이드바에서 고객 선택 (로그인 느낌)
st.sidebar.title("🔐 고객 선택")
user_names = df["name"].tolist()
selected_name = st.sidebar.selectbox("고객 ID를 선택하세요", user_names)

selected_user = df[df["name"] == selected_name].iloc[0]

# 고객 요약 정보 구성
user_context = (
    f"{selected_user['name']}님의 금융 요약 정보입니다:\n"
    f"- 나이: {selected_user['age']}세 | 직업: {selected_user['job']} | 연소득: {selected_user['income']:,}원\n"
    f"- 예상 퇴직 나이: {selected_user['expected_retire_age']}세\n"
    f"🏦 은행 예금: {selected_user['bank_balance']:,}원 | 대출: {selected_user['loan_balance']:,}원\n"
    f"📈 퇴직연금: {selected_user['pension_balance']:,}원 ({selected_user['pension_type']})\n"
    f"📊 주식 투자 경험: {'있음' if selected_user['stock_investment']=='Y' else '없음'}\n"
    f"📊 펀드 투자 경험: {'있음' if selected_user['fund_investment']=='Y' else '없음'}\n"
    f"🛡️ 가입 보험: {selected_user['insurance_list']} | 월 보험료: {selected_user['insurance_monthly_fee']:,}원"
)

st.title("🤖 LangChain Chatbot (FastAPI 연동)")

if "chat_log" not in st.session_state:
    st.session_state.chat_log = []


user_input = st.text_input("You:", key="input")

if user_input:
    # FastAPI 서버로 메시지 POST
    prompt = f"""{user_context.strip()}

    [질문]
    {user_input.strip()}"""

    try:
        response = requests.post(
            "http://localhost:8000/chat",
            json={"message": prompt, "session_id": selected_user["name"]},
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