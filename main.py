# main.py
from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv
import os

# LangChain RAG 관련
from langchain.chains import RetrievalQA
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain_openai import ChatOpenAI  # Chat 모델용 올바른 클래스

# 환경변수 로드
load_dotenv()
API_KEY = os.getenv("OPENAI_API_KEY")

# 1) FAISS 인덱스 로드 (pickle 역직렬화 허용)
emb = OpenAIEmbeddings(openai_api_key=API_KEY)
vs = FAISS.load_local(
    "faiss_index",
    emb,
    allow_dangerous_deserialization=True
)

# 2) RetrievalQA 체인 설정
qa_chain = RetrievalQA.from_chain_type(
    llm=ChatOpenAI(model_name="gpt-3.5-turbo", openai_api_key=API_KEY),
    chain_type="stuff",
    retriever=vs.as_retriever(search_kwargs={"k": 5}),
    return_source_documents=True
)

# FastAPI 앱 및 엔드포인트
app = FastAPI()

class ChatRequest(BaseModel):
    message: str

@app.post("/chat")
def chat(req: ChatRequest):
    result = qa_chain({"query": req.message})
    answer = result["result"]
    # 출처 문서 목록 생성
    sources = sorted({doc.metadata.get("source") for doc in result["source_documents"]})
    citation_block = "\n".join(f"- {os.path.basename(src)}" for src in sources)
    return {
        "response": f"{answer}\n\n📑 출처 문서:\n{citation_block}"
    }
