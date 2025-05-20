## 🟦 **README.md (환경설정, 실행, 문제해결까지 전체 정리본)**

```markdown
# 🟦 퇴직연금 상담 챗봇 (React + Tailwind + FastAPI)

금융 앱(MTS) 스타일의 퇴직연금 상담 챗봇 프론트/백엔드 통합 프로젝트  
- 모바일/웹 반응형 UI  
- Tailwind CSS v3  
- 고객 맞춤형 답변(요약정보 연동)  

---

## 🚩 프로젝트 구조

```

├─ retirement-slm-chatbot/   # React 프론트엔드
│  ├─ src/
│  ├─ tailwind.config.js
│  ├─ postcss.config.cjs
│  ├─ package.json
│  └─ ...
├─ app.py 또는 main.py       # FastAPI 백엔드
├─ requirements.txt         # 백엔드 의존성
├─ .env.example             # 환경변수 예시
└─ README.md                # 프로젝트 가이드

````

---

## 🛠️ 1. 개발 환경 및 설치 가이드

### 💻 사전 요구사항
- Node.js v20.x 이상
- Python 3.9+
- (Windows/Mac/Linux 모두 지원)

### 📦 1-1. 프론트엔드(React) 세팅

```bash
cd retirement-slm-chatbot

# 패키지 설치
npm install

# 개발 서버 실행 (http://localhost:5173)
npm run dev
````

**필수:**

* TailwindCSS v3 (3.4.x), PostCSS, Autoprefixer
* 설정 파일(`tailwind.config.js`, `postcss.config.cjs`)이 반드시 프로젝트 루트에 있어야 함

### 🐍 1-2. 백엔드(FastAPI) 세팅

```bash
# 가상환경(권장)
python -m venv .venv
source .venv/bin/activate   # macOS/Linux
.venv\Scripts\activate      # Windows

# 의존성 설치
pip install -r requirements.txt

# 환경변수 파일 준비
cp .env.example .env
# 또는 직접 .env 파일 생성 후 값 입력

# 서버 실행 (http://localhost:8000)
uvicorn app:app --reload    # (또는 main:app)
```

---

## ⚙️ 2. 환경 변수 설정 (.env)

**프로젝트 루트에 `.env` 파일 생성(아래 예시 참고):**

```
OPEN_API_KEY=sk-여기에-OpenAI-키-입력
LAW_API_KEY=여기에-법률API-키-입력
DART_API_KEY=여기에-다트API-키-입력
```

> 백엔드 및 프론트 연동, 벡터DB 구축 등 모든 AI/외부 API 호출에 필요

---

## 🎨 3. 스타일/빌드 관련 주요 설정

* **TailwindCSS 버전:** v3.x.x (ex. 3.4.3)
* **postcss.config.cjs**
  (확장자에 주의! 프로젝트 루트에 위치)

  ```js
  module.exports = {
    plugins: {
      tailwindcss: {},
      autoprefixer: {},
    },
  };
  ```
* **tailwind.config.js**

  ```js
  module.exports = {
    content: [
      "./index.html",
      "./src/**/*.{js,jsx,ts,tsx}"
    ],
    theme: { extend: {} },
    plugins: [],
  };
  ```
* **src/index.css**

  ```css
  @tailwind base;
  @tailwind components;
  @tailwind utilities;
  ```

---

## 🧑‍💻 4. Troubleshooting (자주 묻는 문제)

* **Tailwind 스타일이 적용 안 될 때**

  * postcss.config.cjs, tailwind.config.js가 루트에 없으면 적용 안 됨
  * 개발 서버(npm run dev) 재시작 필요
* **환경 변수 미설정/키오류**

  * .env 파일 위치/내용 재확인 (키 3개 모두 필요)
* **의존성 설치 오류**

  * Node.js, Python 버전 확인/업데이트
* **FastAPI 실행 오류**

  * requirements.txt, .env 파일 체크
  * 포트 충돌 시 다른 번호 사용 가능(uvicorn app\:app --reload --port 8001 등)

---

## 🔑 5. 커밋/버전관리 가이드

* 주요 변경(프론트/백엔드/설정/문서) 후엔 항상 **루트에서 커밋/푸시**

  ```bash
  git add .
  git commit -m "feat: 챗봇 UI/백엔드 고객정보 연동/환경설정 가이드 등"
  git push origin main
  ```
* .env, node\_modules 등은 반드시 .gitignore에 포함

---

## 📄 6. 기타

* *clone 후 반드시 npm install → npm run dev**


---

````

