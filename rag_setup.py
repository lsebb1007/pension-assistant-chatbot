# rag_setup.py
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS
import os

API_KEY = os.getenv('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')
embeddings = OpenAIEmbeddings(openai_api_key='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')

# 1) PDF 로드
loaders = [PyPDFLoader(f"docs/{fname}") for fname in os.listdir("docs") if fname.endswith(".pdf")]
docs = []
for loader in loaders:
    docs.extend(loader.load())

# 2) 텍스트 청킹
splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
chunks = splitter.split_documents(docs)

# 3) FAISS 인덱스 빌드 (로컬에 저장)
vectorstore = FAISS.from_documents(chunks, embeddings)
vectorstore.save_local("faiss_index")
