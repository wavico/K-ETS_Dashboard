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
import hashlib
from urllib.parse import quote_plus # URL 인코딩을 위한 라이브러리 임포트

# LangChain 및 관련 라이브러리 임포트
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_upstage import UpstageEmbeddings, ChatUpstage
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone, ServerlessSpec
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain import hub

# --- 프로젝트 루트를 sys.path에 추가 ---
# 현재 스크립트(doc_agent.py)의 위치를 기준으로 프로젝트 루트 디렉토리를 계산하여
# 파이썬의 모듈 검색 경로(sys.path)에 추가합니다.
# 이렇게 해야 'prompts'와 같은 다른 패키지를 정상적으로 임포트할 수 있습니다.
try:
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if project_root not in sys.path:
        sys.path.append(project_root)
    
    # 로컬 'prompts' 모듈에서 커스텀 프롬프트 템플릿을 가져옵니다.
    from prompts.interpretation import interpretation_prompt_template
    RAG_PROMPT_TEMPLATE = interpretation_prompt_template
    print("✅ 로컬 커스텀 프롬프트를 성공적으로 불러왔습니다: 'prompts/interpretation.py'")

except (ModuleNotFoundError, ImportError):
    print("⚠️ 로컬 커스텀 프롬프트를 찾을 수 없어 LangChain Hub에서 기본 프롬프트를 가져옵니다.")
    # 로컬 임포트 실패 시, LangChain Hub에서 RAG 프롬프트를 가져오는 것을 대비책으로 사용합니다.
    hub_prompt = "rlm/rag-prompt"
    try:
        RAG_PROMPT_TEMPLATE = hub.pull(hub_prompt)
        print(f"✅ LangChain Hub에서 프롬프트를 성공적으로 불러왔습니다: '{hub_prompt}'")
    except Exception as e:
        print(f"❌ LangChain Hub에서도 프롬프트를 가져오는 데 실패했습니다: {e}")
        # 모든 프롬프트 로딩이 실패할 경우를 대비한 기본 프롬프트
        from langchain_core.prompts import PromptTemplate
        RAG_PROMPT_TEMPLATE = PromptTemplate.from_template(
            "Answer the question based only on the following context:\n{context}\n\nQuestion: {question}"
        )

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

# --- 새로운 헬퍼 함수들 ---

def _calculate_file_hash(filepath: str) -> str:
    """파일의 SHA-256 해시를 계산합니다."""
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(8192):
            sha256.update(chunk)
    return sha256.hexdigest()

def _load_manifest(manifest_path: Path) -> dict:
    """임베딩 기록부(manifest) 파일을 로드합니다."""
    if not manifest_path.exists():
        return {}
    with open(manifest_path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}

def _save_manifest(manifest: dict, manifest_path: Path):
    """임베딩 기록부(manifest) 파일을 저장합니다."""
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=4)

def _delete_vectors_by_filename(index: any, filenames: list[str]):
    """주어진 파일 이름 리스트에 해당하는 벡터들을 Pinecone에서 삭제합니다."""
    if not filenames:
        return
    print(f"\n--- {len(filenames)}개 파일의 기존 벡터를 삭제합니다: {filenames} ---")
    try:
        # Pinecone은 메타데이터를 기반으로 벡터 삭제를 지원합니다.
        # 이를 위해 각 벡터에 'source_file' 메타데이터가 저장되어 있어야 합니다.
        index.delete(filter={"source_file": {"$in": filenames}})
        print("  - ✅ 기존 벡터 삭제 완료.")
    except Exception as e:
        print(f"  - ❌ 벡터 삭제 중 오류 발생: {e}")

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
    
    temp_dir = Path(os.path.dirname(input_file)) / "temp_split"
    temp_dir.mkdir(exist_ok=True)

    try:
        input_pdf = fitz.open(input_file)
    except Exception as e:
        print(f"  ❌ PDF 파일을 여는 중 오류 발생: {e}")
        shutil.rmtree(temp_dir)
        return ""

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

    print("[2/3] Upstage Document API 호출 중...")
    for short_input_file in split_files:
        try:
            with open(short_input_file, "rb") as f:
                response = requests.post(
                    "https://api.upstage.ai/v1/document-digitization",
                    headers={"Authorization": f"Bearer {upstage_api_key}"},
                    data={"base64_encoding": "['figure']", "model": "document-parse"},
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

    print("[3/3] 파싱된 콘텐츠 통합 중...")
    full_html_content = ""
    for json_file in json_files:
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            if "content" in data and data["content"]:
                if isinstance(data["content"], dict):
                    if 'html' in data["content"]:
                        content_text = data["content"]["html"]
                    elif 'text' in data["content"]:
                        content_text = data["content"]["text"]
                    else:
                        content_text = str(data["content"])
                else:
                    content_text = str(data["content"])
                
                full_html_content += content_text
                print(f"  - 성공!!! 콘텐츠 추출: {len(content_text)} 문자")
            else:
                print(f"  - 실패!!! 'content' 키를 찾을 수 없음: {os.path.basename(json_file)}")
        except Exception as e:
            print(f"  - ❌ JSON 파일 처리 중 오류 발생({os.path.basename(json_file)}): {e}")

    print("[4/4] 임시 파일 정리 중...")
    try:
        shutil.rmtree(temp_dir)
        print(f"  - 임시 폴더 삭제 완료: {temp_dir}")
    except Exception as e:
        print(f"  - ❌ 임시 폴더 삭제 중 오류 발생: {e}")

    print(f"--- 단일 PDF 처리 완료 - Total: {len(full_html_content)} 문자 ---")
    return full_html_content

def get_document_splits(html_content: str, source_filename: str, chunk_size: int, chunk_overlap: int) -> list[Document]:
    """
    HTML 콘텐츠를 Document 객체로 변환하고 청크로 분할합니다.
    이제 각 청크에 원본 파일 이름을 메타데이터로 추가합니다.
    """
    print(f"\n--- 문서 처리 시작: {source_filename} ---")
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    
    doc = Document(page_content=html_content, metadata={"source_file": source_filename})
    
    document_list = text_splitter.split_documents([doc])
    print(f"  - 문서를 총 {len(document_list)}개의 청크로 분할했습니다.")
    return document_list

def setup_vector_store(index_name: str, pinecone_api_key: str) -> tuple[any, PineconeVectorStore]:
    """Pinecone 인덱스에 연결하고, LangChain VectorStore 객체를 반환합니다."""
    print("\n--- 벡터 저장소 설정 시작 ---")
    pc = Pinecone(api_key=pinecone_api_key)
    
    # Pinecone 인덱스 존재 여부 확인 후, 없으면 새로 생성
    if index_name not in pc.list_indexes().names():
        print(f"  - '{index_name}' 인덱스가 존재하지 않아 새로 생성합니다.")
        pc.create_index(
            name=index_name,
            dimension=4096,  # Solar-Mini 임베딩 모델의 차원
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1"),
        )
        print("  - 인덱스 생성 완료.")
    else:
        print(f"  - 기존 '{index_name}' 인덱스를 사용합니다.")
    
    index = pc.Index(index_name)
    vector_store = PineconeVectorStore(index=index, embedding=UpstageEmbeddings(model="embedding-query"))
    print("  - 벡터 저장소 설정 완료.")
    return index, vector_store

def create_rag_chain(vectorstore: PineconeVectorStore):
    """LangChain Expression Language(LCEL)를 사용하여 RAG 체인을 생성합니다."""
    print("\n--- LCEL을 사용하여 RAG 체인 생성 중 ---")
    
    llm = ChatUpstage(temperature=0)
    retriever = vectorstore.as_retriever(search_kwargs={"k": 4})
    
    def format_docs(docs):
        """검색된 문서들을 하나의 문자열로 결합합니다."""
        return "\n\n".join(doc.page_content for doc in docs)

    rag_chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | RAG_PROMPT_TEMPLATE
        | llm
        | StrOutputParser()
    )
    
    print("  - RAG 체인이 성공적으로 생성되었습니다.")
    print(f"  - 리트리버는 상위 {retriever.search_kwargs['k']}개의 유사 문서를 검색합니다.")
    return rag_chain

def main():
    """메인 실행 함수"""
    start_total_time = time.time()
    
    try:
        # --- 초기 설정 ---
        project_root = find_project_root()
        upstage_api_key, pinecone_api_key = setup_environment()
        docs_folder = project_root / "docs"
        manifest_path = project_root / "agent" / "embedding_manifest.json"
        
        index_name = "carbon-rag"
        batch_size = 10
        chunk_size = 1000
        chunk_overlap = 200
        pinecone_batch_size = 20

        # --- 벡터 저장소 설정 ---
        index, vectorstore = setup_vector_store(index_name, pinecone_api_key)
        
        # --- 파일 변경 감지 및 처리 ---
        manifest = _load_manifest(manifest_path)
        all_pdf_files = {str(p) for p in docs_folder.glob("*.pdf")}
        processed_files = set(manifest.keys())

        new_files = []
        modified_files = []
        for pdf_path in all_pdf_files:
            current_hash = _calculate_file_hash(pdf_path)
            if pdf_path not in manifest:
                new_files.append(pdf_path)
                manifest[pdf_path] = current_hash
            elif manifest[pdf_path] != current_hash:
                modified_files.append(pdf_path)
                manifest[pdf_path] = current_hash
        
        deleted_files = processed_files - all_pdf_files
        
        # --- 변경된 파일 처리 ---
        files_to_re_embed = new_files + modified_files
        files_to_delete = modified_files + list(deleted_files)

        if not files_to_re_embed and not files_to_delete:
            print("\n✅ 모든 문서가 최신 상태입니다. 임베딩을 건너뛰었습니다.")
        else:
            _delete_vectors_by_filename(index, [os.path.basename(f) for f in files_to_delete])

            if files_to_re_embed:
                print(f"\n--- 총 {len(files_to_re_embed)}개의 신규/수정 파일을 처리합니다 ---")
                for pdf_path in files_to_re_embed:
                    start_file_time = time.time()
                    filename = os.path.basename(pdf_path)
                    
                    html_content = parse_pdf_with_upstage(pdf_path, batch_size, upstage_api_key)
                    if not html_content:
                        continue
                    
                    documents = get_document_splits(html_content, filename, chunk_size, chunk_overlap)
                    
                    print(f"  - {len(documents)}개 청크를 Pinecone에 업로드합니다...")
                    for i in range(0, len(documents), pinecone_batch_size):
                        batch = documents[i:i + pinecone_batch_size]
                        vectorstore.add_documents(batch)
                        print(f"    - Batch {i//pinecone_batch_size + 1} 업로드 완료: {len(batch)}개 청크")

                    print(f"  - ✅ 임베딩 및 업로드 완료: {filename}")
                    file_time = time.time() - start_file_time
                    print(f"  - 처리 시간: {file_time:.2f}초")

            _save_manifest(manifest, manifest_path)
            print("\n✅ 동기화 완료! 임베딩 기록부를 최신 상태로 업데이트했습니다.")

        # --- RAG 체인 생성 및 테스트 ---
        rag_chain = create_rag_chain(vectorstore)
        
        print("\n--- RAG Q&A 테스트 시작 ---")
        question = "온실가스 배출량 산정을 위한 자료를 제출하지 아니하거나 거짓으로 제출한 경우 과태료는?"
        print(f"\n[Question]: {question}\n")
        answer = rag_chain.invoke(question)
        print(f"[Answer]:\n{answer}")

    except (ValueError, FileNotFoundError) as e:
        print(f"\n❌ 치명적 오류 발생: {e}")
    except Exception as e:
        print(f"\n❌ 예상치 못한 오류가 발생했습니다: {e}")
    finally:
        total_time = time.time() - start_total_time
        print(f"\n--- 스크립트 실행 완료 ---")
        print(f"총 실행 시간: {total_time:.2f}초")

if __name__ == "__main__":
    main() 