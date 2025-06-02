import pickle

with open('faiss_index/index.pkl', 'rb') as f:
    vectordb = pickle.load(f)

# tuple인 경우 첫 요소만 사용
if isinstance(vectordb, tuple):
    vectordb = vectordb[0]

# vectordb._dict가 실제 문서 dictionary
docs = []
for v in vectordb._dict.values():
    # 만약 v가 langchain 문서 객체면 page_content 속성 사용
    text = getattr(v, 'page_content', None)
    if text is None:
        # 아니면 그냥 str로 변환
        text = str(v)
    docs.append(text)

# 파일로 저장
with open('rag_documents.txt', 'w', encoding='utf-8') as f:
    for doc in docs:
        f.write(doc.replace('\n', ' ') + '\n')
