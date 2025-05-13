import os
from dotenv import load_dotenv
from langchain.document_loaders import PyPDFLoader, TextLoader, UnstructuredURLLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS

# 환경변수 로드
load_dotenv()
API_KEY = os.getenv("OPENAI_API_KEY")

# 1) 원본 문서 로드
docs = []

# 1-1) PDF 파일 로드
pdf_dir = "docs"
for fname in os.listdir(pdf_dir):
    if fname.lower().endswith(".pdf"):
        loader = PyPDFLoader(os.path.join(pdf_dir, fname))
        docs.extend(loader.load())

# 1-2) 로컬 텍스트(법령 전문) 로드
law_dir = os.path.join("docs", "laws")
if os.path.isdir(law_dir):
    for fname in os.listdir(law_dir):
        if fname.lower().endswith(".txt"):
            loader = TextLoader(os.path.join(law_dir, fname), encoding="utf-8")
            docs.extend(loader.load())

# 1-3) GitHub에 올려둔 법령 전문(raw URL) 로드
law_urls = [
    # 예시: 본인의 GitHub raw URL로 대체
    "https://raw.githubusercontent.com/USERNAME/REPO/main/국민연금법.txt",
    "https://raw.githubusercontent.com/USERNAME/REPO/main/근로자퇴직연금보장법.txt",
]
if law_urls:
    url_loader = UnstructuredURLLoader(law_urls)
    docs.extend(url_loader.load())

# 2) 텍스트 청킹
splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200
)
chunks = splitter.split_documents(docs)

# 3) 임베딩 생성 및 FAISS 벡터 DB 구축
embeddings = OpenAIEmbeddings(openai_api_key=API_KEY)
vectorstore = FAISS.from_documents(chunks, embeddings)
# 로컬에 인덱스 저장
vectorstore.save_local("faiss_index")

print("✅ RAG 벡터 인덱스 생성 완료: faiss_index 폴더에 저장됨")
