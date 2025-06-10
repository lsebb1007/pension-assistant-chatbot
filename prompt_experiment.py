import requests
import time
import pandas as pd



# ==== 1. 실험용 질문 세트 ====
questions = [
#    "실물이전 신청하면 녹취 전화는 누구한테 가나?",
#    "DC에 보유 중인 ETF는 퇴직 시 IRP로 그대로 실물이전 못하나?",
#    "DC형 가입자가 IRP를 거쳐 우회적으로 실물이전을 하는 방법은 무엇인가요?",
    "보유한 상품 중 일부만 선택해서 실물이전할 수 있나요?",
    "기존 퇴직연금 계좌에서 현금은 남겨두고 실물만 이전할 수 있나요?",
    "나는 국민은행에서 신한은행으로 실물이전하고 싶은데 현재 은행에 신한은행 정기예금으로 운용되고 있어, 실물이전은 정기예금이어서 가능한가?",
    "회사에 대표 한 명 있는데 퇴직연금 가입 가능한가요?",
    "법인세 절감 효과를 극대화하려면 DC vs DB 중 어떤 제도가 유리한가?",
    "근로복지공단의 DC는 다른 은행 DC로 실물이전 할 수 있나?",
    "표준형 DC는 다른 은행 DC로 실물이전 할 수 있나?",
#    "신한은행에 뭐뭐 이티에프 잇어?",
#    "DB 재정검증 부족 업체는 2025년 6월 30일까지 금액을 맞춰 넣으면 부족이 해소되나요?",
#    "DB제도에서 예금자보호는 얼마까지 되는가요?",
#    "DB제도에서 저축은행 정기예금에 투자 시 예금자보호는 얼마까지 되는가?",
#    "IRP 연금 수령 시 퇴직소득세 절감 효과는 어떤게 있어?",
#    "DC 계좌와 IRP 계좌 각각 동일한 저축은행 정기예금을 보유 중일 때, 예금자보호는 각각 적용되나요?",
#    "디폴트옵션(Default Option)을 선택하면 이걸로 바로 운용이 되는 건가요?",
#    "디폴트옵션으로 바로 가입하고 싶으면 어떻게 해야 하나요?",
#    "DB제도에서 일부 금액만 이전하려면, 수관회사에서 신청해야 하나요? 이관회사에서 하나요?",
#    "퇴직연금 신규가입과 대출(퇴직연금 담보대출)을 동시에 진행할 때 제한이 있나요?",
#    "퇴직연금 수수료는 어떤 금액을 기준으로 산정하나요?",
#    "임원 퇴직연금도 ‘연간 보수 한도’ 내에서만 납입해야 하나요?",
#    "퇴직 시 퇴직금을 반드시 IRP로 입금해야 하나요?",
#    "DB를 먼저 만든 업체가 DC를 추가로 만들면, 장기계약 할인율은 DB 도입 시점으로 적용되나요?",
#    "DB, DC 제도가 모두 열린 회사는 혼합형 DC인가요?",
#    "DC제도 고객이 DB로 다시 바꾸고 싶다고 하는데, 가능한가요?",
#    "표준형 DC를 실물이전으로 받아올 수 있나요?",
    # 필요한만큼 추가
]

# ==== 2. 프롬프트 엔지니어링 유형(자유롭게 교체/추가) ====
PROMPT_TEMPLATES = {
    "basic": """
당신은 대한민국 은행에서 일하는 퇴직연금 전문 상담사입니다.
아래의 고객 질문에 대해, 퇴직연금 제도(실물이전, 상품 추천, 퇴직금 계산, 중도인출 등)에 대해
정확하고 친절하게 안내해 주세요.
[질문] {question}
""",

    "cot": """
당신은 퇴직연금에 특화된 금융상담 전문가입니다.
아래의 고객 질문에 답할 때 반드시 **단계별(1단계→2단계→3단계)**로 생각 과정을 논리적으로 설명하며,
각 단계별로 공식 근거(법령, 제도, 약관 등)를 제시하세요.

[질문] {question}

(답변 예시)
1단계: 질문의 핵심 쟁점 확인  
2단계: 관련 법규/내규/약관 등 근거 자료 제시  
3단계: 위 근거를 바탕으로 결론 및 실무 안내
""",

    "cove": """
당신은 대한민국 퇴직연금 전문 상담사입니다.
아래 질문에 답할 때, 반드시 다음과 같이 **사실→추론→최종 결론** 3단계로 구분해서 답변하세요:

1. [사실 검증 단계]  
- 질문과 관련된 공식 법령, 약관, 정책 등 핵심 근거를 명확히 나열하세요.
2. [추론 단계]  
- 위 사실을 바탕으로 논리적으로 결론을 도출하세요.
3. [최종 결론]  
- 근거와 추론 결과를 토대로, 고객 질문에 대한 최종 답변을 한 문장으로 요약하세요.

모든 단계는 번호로 구분해서 작성하세요.
[질문] {question}
""",

    "cok": """
당신은 퇴직연금/연금/세무 분야의 여러 전문가들의 의견을 종합해 상담을 제공하는 역할입니다.
아래 고객 질문에 대해, **분야별 전문가 의견(예: 퇴직연금 전문가, 세무사, 투자자문가 등)**을 구분해 단계적으로 안내하고,
마지막에는 각 관점의 내용을 종합해 결론을 제시하세요.

(답변 예시)
- [퇴직연금 전문가 관점] ...
- [세무 전문가 관점] ...
- [투자자문가 관점] ...
- [최종 종합] 각 관점 내용을 바탕으로 결론 도출

[질문] {question}
""",
}


# ==== 3. API URL/세션ID ====
API_URL = "http://localhost:8000/chat"   # FastAPI 기본 포트(수정 가능)
SESSION_ID_PREFIX = "prompt_exp"

RAG_TYPES = ["r0", "r1", "r2", "r3", "full"]

# ==== 4. 결과 저장 ====
results = []

for q_idx, question in enumerate(questions, 1):
    for rag_type in RAG_TYPES:
        for prompt_type, template in PROMPT_TEMPLATES.items():
            print(f"실험: Q{q_idx}, RAG[{rag_type}], PROMPT[{prompt_type}]")
            prompt = template.format(question=question)
            session_id = f"{SESSION_ID_PREFIX}_{q_idx}_{rag_type}_{prompt_type}"
            start_time = time.time()
            try:
                response = requests.post(
                    API_URL,
                    json={
                        "message": prompt,
                        "session_id": session_id,
                        "rag_type": rag_type
                    },
                    timeout=60
                )
                elapsed = round(time.time() - start_time, 2)
                answer = response.json().get("response", "")
            except Exception as e:
                elapsed = None
                answer = f"❌ 오류: {e}"

            context_included = "[근거]" in prompt or "법령" in prompt or "근거" in prompt

            results.append({
                "질문번호": q_idx,
                "질문": question,
                "RAG타입": rag_type,
                "프롬프트유형": prompt_type,
                "프롬프트": prompt,
                "답변": answer,
                "답변길이": len(answer),
                "응답시간(s)": elapsed,
                "근거포함(자동)": "Y" if context_included else "N"
            })
            print(f"실험 완료: Q{q_idx}, RAG[{rag_type}], PROMPT[{prompt_type}]")

df = pd.DataFrame(results)
output_csv = "pesion-assistant-chatbot-experiment_20250605_4o_part2.csv"
df.to_csv(output_csv, index=False, encoding="utf-8-sig")
print(f"✅ 실험 결과가 '{output_csv}' 파일로 저장되었습니다.")
