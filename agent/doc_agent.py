"""
문서 파싱 및 벡터 저장소 구축 스크립트

이 스크립트는 'docs' 폴더에 있는 PDF 문서들을 처리하여 LangChain과 Pinecone을 사용한 RAG 시스템의 기반을 구축합니다.

실행 순서:
1. 'docs' 폴더에서 PDF 파일들을 찾습니다.
2. Upstage Document AI API를 사용하여 각 PDF를 지능적으로 파싱하고 HTML로 변환합니다.
   - 큰 PDF는 작은 페이지 묶음으로 자동 분할하여 처리합니다.
3. 파싱된 HTML 콘텐츠를 의미 있는 단위(청크)로 분할합니다.
4. Upstage 임베딩 모델을 사용하여 각 청크를 벡터로 변환합니다.
5. 변환된 벡터를 Pinecone 벡터 저장소의 'carbon-rag' 인덱스에 저장합니다.
   - 스크립트 실행 시 기존 인덱스는 삭제하고 새로 생성하여 항상 최신 상태를 유지합니다.
"""

import os
import sys
import time
import fitz  # PyMuPDF
import requests
import json
from glob import glob
from dotenv import load_dotenv
from pathlib import Path
import shutil

# LangChain 및 관련 라이브러리 임포트
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_upstage import UpstageEmbeddings, ChatUpstage
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone, ServerlessSpec
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain import hub

# --- 1. 환경 설정 및 상수 정의 ---

def setup_environment():
    """환경 변수를 로드하고 API 키의 유효성을 검사합니다."""
    load_dotenv()
    upstage_api_key = os.getenv("UPSTAGE_API_KEY")
    pinecone_api_key = os.getenv("PINECONE_API_KEY")
    if not upstage_api_key or not pinecone_api_key:
        raise ValueError("API 키가 .env 파일에 설정되어야 합니다: UPSTAGE_API_KEY, PINECONE_API_KEY")
    return upstage_api_key, pinecone_api_key

def find_project_root() -> Path:
    """스크립트 위치를 기반으로 프로젝트 루트 디렉토리를 찾습니다."""
    # __file__은 현재 실행 중인 스크립트의 경로를 나타냅니다.
    current_path = Path(__file__).resolve()
    # 프로젝트의 마커 파일들을 기준으로 루트 디렉토리를 탐색합니다.
    for parent in current_path.parents:
        if (parent / "requirements.txt").exists() and (parent / "chatbot_app.py").exists():
            return parent
    raise FileNotFoundError("프로젝트 루트 디렉토리를 찾을 수 없습니다. 'requirements.txt'와 'chatbot_app.py'가 있는지 확인하세요.")

# --- 2. 문서 전처리 (PDF 파싱) ---

def get_pdf_files(docs_folder: Path) -> list[str]:
    """지정된 폴더에서 모든 PDF 파일의 경로를 찾아 리스트로 반환합니다."""
    if not docs_folder.exists():
        raise FileNotFoundError(f"문서 폴더를 찾을 수 없습니다: {docs_folder}")
    
    pdf_files = list(docs_folder.glob("*.pdf"))
    if not pdf_files:
        raise ValueError(f"문서 폴더에 PDF 파일이 없습니다: {docs_folder}")
    
    print(f"총 {len(pdf_files)}개의 PDF 파일을 발견했습니다:")
    for i, pdf_file in enumerate(pdf_files, 1):
        file_size_mb = pdf_file.stat().st_size / (1024 * 1024)
        print(f"  {i}. {pdf_file.name} ({file_size_mb:.1f} MB)")
    
    return [str(f) for f in pdf_files]

def parse_pdf_with_upstage(input_file: str, batch_size: int, upstage_api_key: str) -> str:
    """Upstage API를 사용하여 단일 PDF 파일을 HTML로 파싱합니다."""
    print(f"\n--- PDF 처리 시작: {os.path.basename(input_file)} ---")
    
    # 임시 분할 파일들을 저장할 폴더 생성
    temp_dir = Path(os.path.dirname(input_file)) / "temp_split"
    temp_dir.mkdir(exist_ok=True)

    try:
        input_pdf = fitz.open(input_file)
    except Exception as e:
        print(f"  ❌ PDF 파일을 여는 중 오류 발생: {e}")
        shutil.rmtree(temp_dir)
        return ""

    # 1단계: PDF를 작은 페이지 묶음으로 분할
    print(f"[1/3] PDF를 {batch_size} 페이지 단위로 분할 중...")
    split_files, json_files = [], []
    num_pages = len(input_pdf)
    for start_page in range(0, num_pages, batch_size):
        end_page = min(start_page + batch_size - 1, num_pages - 1)
        output_path = temp_dir / f"{Path(input_file).stem}_{start_page}_{end_page}.pdf"
        with fitz.open() as output_pdf:
            output_pdf.insert_pdf(input_pdf, from_page=start_page, to_page=end_page)
            output_pdf.save(str(output_path))
        split_files.append(str(output_path))
    input_pdf.close()
    print(f"  - {len(split_files)}개의 파일로 분할 완료.")

    # 2단계: 분할된 각 파일에 대해 Upstage API 호출
    print("[2/3] Upstage Document API 호출 중...")
    for short_input_file in split_files:
        try:
            with open(short_input_file, "rb") as f:
                response = requests.post(
                    "https://api.upstage.ai/v1/document-digitization",
                    headers={"Authorization": f"Bearer {upstage_api_key}"},
                    data={"ocr": "true"},  # OCR 옵션 활성화
                    files={"document": f},
                )
            response.raise_for_status()
            
            json_output_file = Path(short_input_file).with_suffix(".json")
            with open(json_output_file, "w", encoding="utf-8") as f:
                json.dump(response.json(), f, ensure_ascii=False, indent=4)
            json_files.append(str(json_output_file))
            print(f"  - API 응답 저장: {json_output_file.name}")
        except requests.exceptions.RequestException as e:
            print(f"  - ❌ API 호출 오류 ({Path(short_input_file).name}): {e}")

    # 3단계: JSON 결과에서 HTML 콘텐츠 통합
    print("[3/3] 파싱된 콘텐츠 통합 중...")
    full_html_content = ""
    for json_file in json_files:
        with open(json_file, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                html_part = data.get("html", "")
                if html_part:
                    full_html_content += html_part
                    print(f"  - 콘텐츠 추가: {Path(json_file).name} ({len(html_part):,} 자)")
            except json.JSONDecodeError:
                print(f"  - ❌ JSON 파일 파싱 오류: {Path(json_file).name}")
    
    # 임시 파일 및 폴더 삭제
    shutil.rmtree(temp_dir)
    
    print(f"--- PDF 처리 완료. 총 {len(full_html_content):,} 자의 HTML 콘텐츠 추출 ---")
    return full_html_content

def parse_all_pdfs(pdf_files: list[str], batch_size: int, upstage_api_key: str) -> str:
    """여러 PDF 파일을 순차적으로 처리하고 모든 HTML 콘텐츠를 통합합니다."""
    print(f"\n--- 총 {len(pdf_files)}개 PDF 파일의 전체 파싱을 시작합니다 ---")
    all_html_content = ""
    for i, file_path in enumerate(pdf_files, 1):
        print(f"\n>>> 파일 {i}/{len(pdf_files)} 처리 중: {os.path.basename(file_path)}")
        html_content = parse_pdf_with_upstage(file_path, batch_size, upstage_api_key)
        if html_content:
            separator = f"\\n\\n<hr><h1>문서: {os.path.basename(file_path)}</h1><hr>\\n\\n"
            all_html_content += separator + html_content
    print(f"\n--- 모든 PDF 처리 완료. 총 콘텐츠 길이: {len(all_html_content):,} 자 ---")
    return all_html_content

# --- 3. LangChain을 이용한 벡터 저장소 구축 ---

def get_document_splits(html_content: str, chunk_size: int, chunk_overlap: int) -> list[Document]:
    """HTML 콘텐츠를 Document 객체로 변환하고 청크로 분할합니다."""
    print("\n--- LangChain 문서 처리 시작 ---")
    doc = Document(page_content=html_content, metadata={"source": "parsed_pdf_documents"})
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\\n\\n", "\\n", ". ", " ", ""]
    )
    
    document_list = text_splitter.split_documents([doc])
    print(f"  - 문서를 총 {len(document_list)}개의 청크로 분할했습니다.")
    avg_chunk_len = len(html_content) // len(document_list) if document_list else 0
    print(f"  - 평균 청크 크기: {avg_chunk_len:,} 자")
    return document_list

def setup_vector_store(document_list: list[Document], index_name: str, pinecone_api_key: str) -> PineconeVectorStore:
    """문서 청크를 임베딩하고 Pinecone 벡터 저장소를 생성 및 초기화합니다."""
    print("\n--- 벡터 저장소 설정 시작 ---")
    
    embeddings = UpstageEmbeddings(model="solar-1-mini-embedding")
    print(f"  - 임베딩 모델: solar-1-mini-embedding (차원: {embeddings.client.embedding_dimension})")

    pc = Pinecone(api_key=pinecone_api_key)
    
    # 기존 인덱스가 있다면 삭제하여 최신 상태 유지
    if index_name in pc.list_indexes().names():
        print(f"  - 기존 '{index_name}' 인덱스를 삭제합니다.")
        pc.delete_index(index_name)
        time.sleep(5)  # 삭제 후 안정화를 위해 잠시 대기
    
    # 새 인덱스 생성
    print(f"  - 새 '{index_name}' 인덱스를 생성합니다.")
    pc.create_index(
        name=index_name,
        dimension=embeddings.client.embedding_dimension,
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region="us-east-1")
    )

    # 문서를 벡터화하여 인덱스에 저장
    print(f"  - {len(document_list)}개의 문서를 인덱스에 저장합니다...")
    vector_store = PineconeVectorStore.from_documents(
        documents=document_list,
        embedding=embeddings,
        index_name=index_name
    )
    print("  - ✅ 벡터 저장소 설정 및 데이터 저장이 완료되었습니다.")
    return vector_store

# --- 4. 메인 실행 로직 ---

def main():
    """스크립트의 메인 실행 함수"""
    # 상수 정의
    INDEX_NAME = "carbon-rag"
    CHUNK_SIZE = 1500
    CHUNK_OVERLAP = 200
    PDF_BATCH_SIZE = 10

    try:
        # 1. 환경 설정
        upstage_api_key, pinecone_api_key = setup_environment()
        project_root = find_project_root()
        docs_folder = project_root / "docs"
        print(f"프로젝트 루트: {project_root}")
        
        # 2. 문서 파싱
        pdf_files = get_pdf_files(docs_folder)
        html_content = parse_all_pdfs(pdf_files, PDF_BATCH_SIZE, upstage_api_key)
        if not html_content:
            raise ValueError("PDF 파일에서 콘텐츠를 추출하지 못했습니다.")
        
        # 3. 문서 분할
        document_splits = get_document_splits(html_content, CHUNK_SIZE, CHUNK_OVERLAP)

        # 4. 벡터 저장소 구축
        setup_vector_store(document_splits, INDEX_NAME, pinecone_api_key)
        
        print("\n🎉 모든 작업이 성공적으로 완료되었습니다!")
        print(f"이제 '{INDEX_NAME}' 인덱스를 RAG 애플리케이션에서 사용할 수 있습니다.")

    except Exception as e:
        print(f"\n❌ 스크립트 실행 중 오류가 발생했습니다: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main() 