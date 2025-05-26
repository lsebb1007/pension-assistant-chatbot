import requests
import time
import pandas as pd

# ==== 1. 실험용 질문 세트 ====
questions = [
    "신한은행으로 irp 실물이전 하고싶은데, 내가 보유하고 있는 이상품들 실물이전 가능한지 확인해줘. ",
    "이번달 퇴직연금 원리금보장 상품 추천해줘. ",
    "나의 미납퇴직금은 어떻게 계산해야할 까? 그리고 미납퇴직금이 있으면 어떤 방식으로 회사한테 받아야할까",
    "퇴직연금 중도인출 시 인출 가능한 금액 제한이 있어?",
    "퇴직연금 상품 유형별 장단점을 정리해줘.",
    "내가 dc 퇴직금 지급 신청하면 언제쯤 받을 수 있어? ",
    "실물이전으로 신청했는데 만약 실물이전 불가한 상품을 일부 보유하고 있으면 어떻게해? ",
    "신한은행에 있는 퇴직연금 etf 종류 좀 알 수 있을까?",
    "현재 dc에 있는 etf를 퇴직할 때 irp로 실물이전 할 수 있어?",
    "퇴직연금 중도인출 관련해서, 나는 현재 무주택자이고, 주택구입자금용으로 받으려면 주택을 꼭 내 명의로 사야해? "
    # 필요한만큼 추가
]

# ==== 2. 프롬프트 엔지니어링 유형(자유롭게 교체/추가) ====
PROMPT_TEMPLATES = {
    "basic": "{question}",
    "role": "너는 퇴직연금 전문 상담사야. 아래 질문에 전문가답게 답해줘.\n[질문]\n{question}",
    "fewshot": """Q: 퇴직연금이란 무엇인가요?
A: 퇴직연금은 근로자의 퇴직 후 노후를 대비해 사용되는 제도입니다.

Q: IRP와 DC형의 차이는?
A: IRP는 개인퇴직계좌로, 개인이 직접 운용하며 DC형은 회사가 납입한 금액을 근로자가 운용하는 방식입니다.

Q: {question}
A:""",
    "cot": "{question}\n질문에 답할 때, 반드시 단계별로 생각 과정을 설명해줘.",
    "context": "질문에 답할 때 관련 법령의 조항이나 실제 퇴직연금 약관을 근거로 삼아 구체적으로 답해줘. [질문] {question}",
}

# ==== 3. API URL/세션ID ====
API_URL = "http://localhost:8000/chat"   # FastAPI 기본 포트(수정 가능)
SESSION_ID_PREFIX = "prompt_exp"

# ==== 4. 결과 저장 ====
results = []

for q_idx, question in enumerate(questions, 1):
    for prompt_type, template in PROMPT_TEMPLATES.items():
        prompt = template.format(question=question)
        session_id = f"{SESSION_ID_PREFIX}_{q_idx}_{prompt_type}"

        # 응답 측정
        start_time = time.time()
        try:
            response = requests.post(
                API_URL,
                json={
                    "message": prompt,
                    "session_id": session_id
                },
                timeout=60
            )
            elapsed = round(time.time() - start_time, 2)
            answer = response.json().get("response", "")
        except Exception as e:
            elapsed = None
            answer = f"❌ 오류: {e}"

        # "근거 포함" 체크 자동화: "[근거]" 문자열 등장 여부로 1차 판별
        context_included = "[근거]" in prompt or "법령" in prompt or "근거" in prompt

        results.append({
            "질문번호": q_idx,
            "질문": question,
            "프롬프트유형": prompt_type,
            "프롬프트": prompt,
            "답변": answer,
            "답변길이": len(answer),
            "응답시간(s)": elapsed,
            "근거포함(자동)": "Y" if context_included else "N"
            # 👆 실제 근거 포함 여부/정답/환각/코멘트는 사람이 추가 평가
        })

# ==== 5. 결과 CSV로 저장 ====
df = pd.DataFrame(results)
output_csv = "prompt_experiment_results.csv"
df.to_csv(output_csv, index=False, encoding="utf-8-sig")
print(f"✅ 실험 결과가 '{output_csv}' 파일로 저장되었습니다.")
