import os
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader, TextLoader, UnstructuredURLLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores.faiss import FAISS
from tqdm import tqdm

# 환경변수 로드
load_dotenv()
API_KEY = os.getenv("OPENAI_API_KEY")

# 1) 원본 문서 로드
docs = []

# 1-1) PDF 파일 로드
pdf_dir = "docs_r1"
for fname in os.listdir(pdf_dir):
    if fname.lower().endswith(".pdf"):
        loader = PyPDFLoader(os.path.join(pdf_dir, fname))
        docs.extend(loader.load())

# 1-2) 로컬 텍스트(.txt, .md) 로드
law_dir = os.path.join("docs_r1", "laws")
if os.path.isdir(law_dir):
    for fname in os.listdir(law_dir):
        if fname.lower().endswith((".txt", ".md")):
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

# 3) 임베딩 생성 (배치 처리)
embeddings = OpenAIEmbeddings(openai_api_key=API_KEY)

all_embeddings = []
batch_size = 100

print(f"총 {len(chunks)}개 청크를 {batch_size}개씩 임베딩합니다...")

for i in tqdm(range(0, len(chunks), batch_size)):
    batch = chunks[i:i+batch_size]
    texts = [doc.page_content for doc in batch]
    vectors = embeddings.embed_documents(texts)
    all_embeddings.extend(vectors)

# 4) FAISS 벡터 DB 구축 및 저장
text_embedding_pairs = list(zip([doc.page_content for doc in chunks], all_embeddings))
vectorstore = FAISS.from_embeddings(
    text_embedding_pairs,
    embeddings  # OpenAIEmbeddings 객체
)
vectorstore.save_local("faiss_index_r1")

print("✅ RAG 벡터 인덱스 생성 완료: faiss_index_r1 폴더에 저장됨")