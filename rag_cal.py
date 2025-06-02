import pandas as pd
from sentence_transformers import SentenceTransformer, util
import numpy as np
import re

# 1. 문서 불러오기
with open('docs_temp.csv', encoding='utf-8') as f:
    docs = [line.strip() for line in f if line.strip()]

# 2. 답변 데이터
df = pd.read_csv('prompt_experiment_results.csv')
df['답변'] = df['답변'].fillna('').astype(str)

# 3. 문장 분리
def split_sentences(text):
    return [s.strip() for s in re.split(r'(?<=[.!?])\s+|\n', text) if s.strip()]

# 4. 임베딩 모델 로드
model = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')

# 5. 문서 임베딩 (최초 1회만, 시간이 걸림)
doc_embeds = model.encode(docs, convert_to_tensor=True, show_progress_bar=True)

def answer_includes_rag(answer, doc_embeds, docs, threshold=0.8):
    sents = split_sentences(answer)
    if not sents:
        return False
    sent_embeds = model.encode(sents, convert_to_tensor=True)
    cos_scores = util.cos_sim(sent_embeds, doc_embeds)
    max_sim = np.max(cos_scores.cpu().numpy())
    return max_sim >= threshold

# 6. 전체 답변 근거포함 여부 판정
result_list = []
for idx, row in df.iterrows():
    answer = row['답변']
    has_evidence = answer_includes_rag(answer, doc_embeds, docs, threshold=0.8)
    result_list.append('Y' if has_evidence else 'N')

df['근거포함(RAG기준)'] = result_list

# 7. 프롬프트유형별 근거포함률/응답시간 통계
summary = df.groupby('프롬프트유형').agg(
    total_count=('근거포함(RAG기준)', 'count'),
    근거포함_수=('근거포함(RAG기준)', lambda x: (x == 'Y').sum()),
    근거포함률=('근거포함(RAG기준)', lambda x: 100 * (x == 'Y').mean()),
    평균_응답시간=('응답시간(s)', 'mean'),
)
print(summary)

# 8. 저장(선택)
df.to_csv('prompt_exp_with_rag_label.csv', index=False)
