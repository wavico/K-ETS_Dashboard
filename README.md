# 🌍 K-ETS 통합 관리 시스템: AI 보고서 생성 백엔드

본 프로젝트는 사용자가 입력한 '주제'를 기반으로 전문적인 수준의 보고서를 자동으로 생성하는 FastAPI 백엔드 시스템입니다. 템플릿 생성, 구조화된 목차 변환, 데이터 기반의 본문 생성 및 파일 다운로드(DOCX, PDF)까지 보고서 작성의 전 과정을 자동화합니다.

## 🎯 주요 기능

-   **📝 주제 기반 보고서 구조 생성**: 단일 '주제' 입력만으로 보고서의 표준 템플릿과 JSON 형식의 목차를 자동으로 생성합니다.
-   **✍️ 실시간 컨텐츠 생성 및 스트리밍**: 사용자가 수정한 목차에 따라, 각 섹션의 본문을 실시간으로 생성하여 Server-Sent Events(SSE)로 스트리밍합니다.
-   **💾 다양한 포맷으로 다운로드**: 완성된 보고서를 `DOCX` 또는 `PDF` 파일 형식으로 다운로드할 수 있는 API를 제공합니다.
-   **🧠 다중 에이전트 아키텍처**: 기능별로 전문화된 AI 에이전트(템플릿 생성, 내용 생성)를 활용하여 고품질의 결과물을 보장합니다.

## 🏗️ 시스템 아키텍처

본 백엔드는 FastAPI를 기반으로 구축되었으며, 기능적으로 분리된 두 개의 핵심 AI 에이전트와 상호작용합니다.

1.  **FastAPI 서버 (`main.py`)**: 클라이언트의 요청을 받아 각 에이전트에게 작업을 분배하고, 생성된 결과를 클라이언트에 스트리밍하거나 파일로 제공하는 컨트롤 타워 역할을 합니다.
2.  **템플릿 생성 에이전트 (`agent/agent_template.py`)**: 사용자가 입력한 주제를 분석하여 보고서의 뼈대가 되는 텍스트 템플릿과, UI에서 편집 가능한 JSON 형식의 구조화된 목차를 생성합니다.
3.  **본문 생성 에이전트 (`agent/enhanced_carbon_rag_agent.py`)**: 각 목차 섹션의 제목을 구체적인 질문으로 변환하여, 데이터 분석 및 문서 검색(RAG)을 통해 사실 기반의 상세한 본문을 생성합니다.

## 본문 생성 에이전트 (`agent/enhanced_carbon_rag_agent.py`)

- 각 목차 섹션의 제목을 구체적인 질문으로 변환하여, 데이터 분석 및 문서 검색(RAG)을 통해 사실 기반의 상세한 본문을 생성합니다.
- CSV 데이터를 내부 쿼리로 요청하여 분석하는 기능을 포함하여, 데이터 기반의 인사이트를 제공합니다.
- `doc_agent.py`의 RAG 기반 해석 기능을 활용하여, 문서 기반의 질의응답을 수행하고, 보고서의 본문을 보강합니다.

## ⚙️ API 명세

### `POST /generate-outline-from-topic`

-   **설명**: 주제를 받아 보고서의 템플릿과 구조화된 목차(JSON)를 생성합니다.
-   **요청 본문 (Request Body)**:
    ```json
    {
      "topic": "국내 탄소 배출 현황"
    }
    ```
-   **응답 (Response)**:
    ```json
    {
      "template_text": "제 1장 서론\n1.1. 연구의 배경...",
      "outline": {
        "title": "국내 탄소 배출 현황 분석 및 전망",
        "chapters": [...]
      }
    }
    ```

### `POST /generate-report`

-   **설명**: 사용자가 수정한 최종 목차를 받아, 각 섹션의 내용을 실시간으로 스트리밍합니다.
-   **요청 본문 (Request Body)**:
    ```json
    {
      "topic": "국내 탄소 배출 현황",
      "outline": {
        "title": "...",
        "chapters": [...]
      }
    }
    ```
-   **응답 (Response)**: Server-Sent Events (SSE) 스트림
    ```
    data: {"type": "section_title", "payload": "1.1. 연구의 배경 및 필요성"}
    data: {"type": "content", "payload": "최근 기후 변화는..."}
    ...
    data: {"type": "done", "payload": "보고서 생성이 완료되었습니다."}
    ```

### `POST /download-report`

-   **설명**: 생성된 보고서의 전체 텍스트를 받아 지정된 파일 형식으로 다운로드합니다.
-   **쿼리 파라미터 (Query Parameter)**: `format` (`docx` 또는 `pdf`, 기본값: `docx`)
-   **요청 본문 (Request Body)**:
    ```json
    {
      "title": "나의 첫 보고서",
      "content": "이것은 완성된 보고서의 전체 내용입니다..."
    }
    ```
-   **응답 (Response)**: `.docx` 또는 `.pdf` 파일 다운로드

## 🚀 설치 및 실행

### 1. 의존성 설치

프로젝트 루트 디렉토리에서 아래 명령어를 실행합니다.

```bash
pip install -r requirements.txt
```

### 2. 환경변수 설정 (필수)

`env.example` 파일을 `.env`로 복사한 후, 파일 내의 `UPSTAGE_API_KEY`와 `OPENAI_API_KEY`에 유효한 API 키를 입력해주세요.

```bash
# env.example 파일을 .env로 복사
cp env.example .env
```

### 3. FastAPI 서버 실행

```bash
python main.py
```

서버가 정상적으로 실행되면, 터미널에 `Uvicorn running on http://0.0.0.0:8000` 와 같은 메시지가 나타납니다.

### 4. API 테스트

웹 브라우저에서 `http://127.0.0.1:8000/docs` 로 접속하면, API 엔드포인트를 직접 테스트할 수 있는 Swagger UI 화면을 사용할 수 있습니다.

---
*기존 대시보드에 대한 설명은 `README_FRONTEND.md`에서 확인하실 수 있습니다.*
