"""
문서 기반 RAG 서비스 클래스

FastAPI에서 사용할 수 있도록 수정된 문서 기반 RAG 시스템
PDF 문서 처리, 임베딩, 벡터 저장소 관리 등의 기능을 제공
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
from urllib.parse import quote_plus
import re
from typing import Dict, List, Any, Optional
import logging

# LangChain 및 관련 라이브러리 임포트
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

# --- LLM 및 임베딩 라이브러리 임포트 ---
try:
    from langchain_upstage import UpstageEmbeddings, ChatUpstage
    UPSTAGE_AVAILABLE = True
except ImportError:
    UPSTAGE_AVAILABLE = False

try:
    from langchain_openai import OpenAIEmbeddings, ChatOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    from langchain_pinecone import PineconeVectorStore
    from pinecone import Pinecone, ServerlessSpec
    PINECONE_AVAILABLE = True
except ImportError:
    PINECONE_AVAILABLE = False

try:
    from langchain import hub
    HUB_AVAILABLE = True
except ImportError:
    HUB_AVAILABLE = False

logger = logging.getLogger(__name__)

# 환경변수 로드
load_dotenv()

# 프롬프트 템플릿 로드
try:
    from app.prompts.interpretation import interpretation_prompt_template
    RAG_PROMPT_TEMPLATE = interpretation_prompt_template
    print("DocAgent: 로컬 커스텀 프롬프트를 성공적으로 불러왔습니다")
except (ModuleNotFoundError, ImportError):
    print("DocAgent: 로컬 커스텀 프롬프트를 찾을 수 없어 LangChain Hub에서 기본 프롬프트를 가져옵니다.")
    hub_prompt = "rlm/rag-prompt"
    try:
        RAG_PROMPT_TEMPLATE = hub.pull(hub_prompt)
        print(f"DocAgent: LangChain Hub에서 프롬프트를 성공적으로 불러왔습니다: '{hub_prompt}'")
    except Exception as e:
        print(f"DocAgent: LangChain Hub에서도 프롬프트를 가져오는 데 실패했습니다: {e}")
        from langchain_core.prompts import PromptTemplate
        RAG_PROMPT_TEMPLATE = PromptTemplate.from_template(
            "Answer the question based only on the following context:\n{context}\n\nQuestion: {question}"
        )

class EmbeddingManifestManager:
    """
    임베딩 기록부(embedding_manifest.json)의 관리를 전담하는 클래스.

    - 인덱스별로 파일 임베딩 상태(해시)를 추적합니다.
    - 이전 버전의 manifest 파일을 새로운 구조로 자동 마이그레이션합니다.
    """
    def __init__(self, manifest_path: Path, index_name: str):
        self.manifest_path = manifest_path
        self.index_name = index_name
        self.manifest = self._load_manifest()

    def _load_manifest(self) -> dict:
        """
        Manifest 파일을 로드하고, 필요시 구조를 마이그레이션합니다.
        """
        if not self.manifest_path.exists():
            return {self.index_name: {}}
        try:
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # 이전 버전 manifest 구조 감지 및 마이그레이션
            # 값(value)이 딕셔너리가 아니면 이전 버전으로 간주합니다.
            if data and not isinstance(list(data.values())[0], dict):
                print("이전 버전의 manifest 파일을 감지했습니다. 인덱스별 구조로 자동 마이그레이션합니다.")
                # 'carbon-rag'는 이전 기본값으로 가정하고, 현재 인덱스용 공간을 만듭니다.
                migrated_data = {"carbon-rag": data, self.index_name: {}}
                self.save(migrated_data)
                return migrated_data
            
            if self.index_name not in data:
                data[self.index_name] = {}
            return data
        except (json.JSONDecodeError, IndexError):
            return {self.index_name: {}}

    def save(self, data: dict = None):
        """Manifest 파일에 현재 상태를 저장합니다."""
        if data is None:
            data = self.manifest
        with open(self.manifest_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    def get_file_hash(self, filepath: str) -> Optional[str]:
        """특정 파일의 저장된 해시를 가져옵니다."""
        return self.manifest.get(self.index_name, {}).get(filepath)

    def update_file_hash(self, filepath: str, file_hash: str):
        """파일의 해시를 업데이트합니다."""
        if self.index_name not in self.manifest:
            self.manifest[self.index_name] = {}
        self.manifest[self.index_name][filepath] = file_hash

    def get_processed_files(self) -> set:
        """현재 인덱스에 대해 처리된 모든 파일의 경로 집합을 반환합니다."""
        return set(self.manifest.get(self.index_name, {}).keys())

    def remove_files(self, filepaths: list[str]):
        """Manifest에서 특정 파일 기록을 삭제합니다."""
        if self.index_name in self.manifest:
            for path in filepaths:
                self.manifest[self.index_name].pop(path, None)


class DocumentRAGAgent:
    def __init__(self, index_name="carbon-multiagent"):
        """
        DocumentRAGAgent를 초기화합니다.

        - 환경 변수 로드 및 API 키 검사
        - LLM 및 임베딩 모델 설정
        - Pinecone 벡터 저장소 설정
        - 로컬 문서('docs' 폴더)와 벡터 저장소 간의 동기화 수행
        - RAG 체인 생성
        """
        print("\n--- Document RAG Agent 초기화 시작 ---")
        self.index_name = index_name
        self.rag_chain = None

        try:
            self._setup_environment()
            self._setup_llms_and_embeddings()
            self.project_root = self._find_project_root()
            manifest_path = self.project_root / "agent" / "embedding_manifest.json"
            self.manifest_manager = EmbeddingManifestManager(manifest_path, self.index_name)
            
            # Pinecone 없이 기본 기능만 사용
            self.index = None
            self.vectorstore = None
            self.rag_chain = None
            print("Pinecone 없이 기본 LLM 기능만 사용합니다.")
                
            print("\n--- Document RAG Agent 초기화 완료 ---")
        except Exception as e:
            print(f"\nDocument RAG Agent 초기화 중 치명적 오류 발생: {e}")
            raise

    def _setup_environment(self):
        """환경 변수를 로드하고 API 키의 유효성을 검사합니다."""
        load_dotenv()
        self.upstage_api_key = os.getenv("UPSTAGE_API_KEY")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        
        # LLM API 키는 필수
        if not (self.upstage_api_key or self.openai_api_key):
            raise ValueError("LLM API 키가 .env 파일에 설정되어야 합니다: (UPSTAGE_API_KEY 또는 OPENAI_API_KEY)")
        
        print("LLM API 키 설정 완료. Pinecone 없이 기본 기능만 사용합니다.")

    def _setup_llms_and_embeddings(self):
        """사용 가능한 API 키에 따라 LLM과 임베딩 모델, 차원 수를 설정합니다."""
        if UPSTAGE_AVAILABLE and self.upstage_api_key:
            print("DocAgent: Upstage API 키를 사용합니다.")
            self.llm = ChatUpstage(temperature=0)
            self.embeddings = UpstageEmbeddings(model="embedding-query")
            self.embedding_dimension = 4096  # Upstage 모델의 임베딩 차원
        elif OPENAI_AVAILABLE and self.openai_api_key:
            print("DocAgent: OpenAI API 키를 사용합니다 (Upstage 키 없음).")
            self.llm = ChatOpenAI(model="gpt-4.1-nano", temperature=0)
            self.embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
            self.embedding_dimension = 1536  # text-embedding-3-small 모델의 임베딩 차원
        else:
            raise ValueError("LLM 및 임베딩을 위한 API 키가 없습니다. .env 파일을 확인해주세요.")

    def _find_project_root(self) -> Path:
        """스크립트 위치를 기반으로 프로젝트 루트 디렉토리를 찾습니다."""
        current_path = Path(__file__).resolve()
        for parent in current_path.parents:
            if (parent / "requirements.txt").exists() and (parent / "chatbot_app.py").exists():
                return parent
        raise FileNotFoundError("프로젝트 루트 디렉토리를 찾을 수 없습니다.")

    def _calculate_file_hash(self, filepath: str) -> str:
        """파일의 SHA-256 해시를 계산합니다."""
        sha256 = hashlib.sha256()
        with open(filepath, "rb") as f:
            while chunk := f.read(8192):
                sha256.update(chunk)
        return sha256.hexdigest()

    def _delete_vectors_by_filename(self, filenames: list[str]):
        """Pinecone 없이 벡터 삭제를 건너뜁니다."""
        print("Pinecone 없이 벡터 삭제를 건너뜁니다.")
        return

    def _parse_pdf_with_upstage(self, input_file: str, batch_size: int) -> str:
        """Upstage API를 사용하여 단일 PDF 파일을 HTML로 파싱합니다."""
        print(f"\n--- PDF 처리 시작: {os.path.basename(input_file)} ---")
        temp_dir = Path(os.path.dirname(input_file)) / "temp_split"
        temp_dir.mkdir(exist_ok=True)
        try:
            input_pdf = fitz.open(input_file)
        except Exception as e:
            print(f"  PDF 파일을 여는 중 오류 발생: {e}")
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
                        headers={"Authorization": f"Bearer {self.upstage_api_key}"},
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
                print(f"  - API 호출 오류 ({Path(short_input_file).name}): {e}")
        print("[3/3] 파싱된 콘텐츠 통합 중...")
        full_html_content = ""
        for json_file in json_files:
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if "content" in data and data["content"]:
                    content_text = data["content"].get("html", str(data["content"]))
                    full_html_content += content_text
                    print(f"  - 성공!!! 콘텐츠 추출: {len(content_text)} 문자")
                else:
                    print(f"  - 실패!!! 'content' 키를 찾을 수 없음: {os.path.basename(json_file)}")
            except Exception as e:
                print(f"  - JSON 파일 처리 중 오류 발생({os.path.basename(json_file)}): {e}")
        print("[4/4] 임시 파일 정리 중...")
        try:
            shutil.rmtree(temp_dir)
            print(f"  - 임시 폴더 삭제 완료: {temp_dir}")
        except Exception as e:
            print(f"  - 임시 폴더 삭제 중 오류 발생: {e}")
        print(f"--- 단일 PDF 처리 완료 - Total: {len(full_html_content)} 문자 ---")
        return full_html_content

    def _clean_text(self, text: str) -> str:
        """
        문서 내용에서 불필요한 메타데이터와 공백을 제거하여 텍스트를 정제합니다.

        Args:
            text (str): 정제할 원본 텍스트

        Returns:
            str: 정제된 텍스트
        """
        # [그림 1], [표 1-1], [Figure 1], [Table 1] 과 같은 참조 태그를 제거합니다.
        # 숫자뿐만 아니라 '1-1'과 같은 형태도 처리할 수 있도록 정규식을 구성합니다.
        text = re.sub(r'\[(그림|표|Figure|Table)\s*[\d\.-]+\]', '', text)
        
        # '페이지 10', 'Page 10'과 같은 페이지 번호 표시를 제거합니다.
        text = re.sub(r'(페이지|Page)\s+\d+', '', text)
        
        # 목차 등에서 사용되는 점선(....... )을 제거합니다. 5개 이상 연속될 경우에만 제거합니다.
        text = re.sub(r'\.{5,}', '', text)
        
        # 여러 개의 공백, 줄바꿈, 탭 등 연속적인 공백 문자를 하나의 공백으로 통일합니다.
        # 양 끝의 불필요한 공백도 제거합니다.
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text

    def _get_document_splits(self, html_content: str, source_filename: str, chunk_size: int, chunk_overlap: int) -> list[Document]:
        """HTML 콘텐츠를 정제하고 청크로 분할합니다."""
        print(f"\n--- 문서 처리 및 분할 시작: {source_filename} ---")
        
        # 1. 문서 내용에서 불필요한 요소 제거
        print("  - 텍스트 내용 정제 중...")
        cleaned_content = self._clean_text(html_content)
        original_len = len(html_content)
        cleaned_len = len(cleaned_content)
        reduction_pct = (original_len - cleaned_len) / original_len * 100 if original_len > 0 else 0
        print(f"  - 정제 완료: {original_len}자 -> {cleaned_len}자 ({reduction_pct:.1f}% 감소)")

        # 2. 정제된 콘텐츠를 청크로 분할
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        doc = Document(page_content=cleaned_content, metadata={"source_file": source_filename})
        document_list = text_splitter.split_documents([doc])
        print(f"  - 정제된 문서를 총 {len(document_list)}개의 청크로 분할했습니다.")
        return document_list

    def _setup_vector_store(self) -> tuple[any, any]:
        """Pinecone 없이 기본 기능만 사용합니다."""
        print("\n--- 벡터 저장소 설정 건너뛰기 ---")
        print("Pinecone 없이 기본 LLM 기능만 사용합니다.")
        return None, None

    def _synchronize_documents(self):
        """Pinecone 없이 문서 동기화를 건너뜁니다."""
        print("\n--- 문서 동기화 건너뛰기 ---")
        print("Pinecone 없이 기본 LLM 기능만 사용합니다.")
        return

    def _create_rag_chain(self, vectorstore: any):
        """Pinecone 없이 RAG 체인 생성을 건너뜁니다."""
        print("Pinecone 없이 RAG 체인 생성을 건너뜁니다.")
        return None

    def ask(self, question: str) -> str:
        """
        주어진 질문에 대해 기본 LLM 답변을 생성합니다.

        Args:
            question: 사용자 질문

        Returns:
            LLM이 생성한 답변 문자열
        """
        if not self.llm:
            return "LLM이 초기화되지 않았습니다. 에이전트 초기화 중 오류가 발생했을 수 있습니다."
        
        print(f"\n--- DocumentRAGAgent.ask() 호출: '{question}' ---")
        try:
            # 간단한 프롬프트로 LLM에 질문
            prompt = f"다음 질문에 대해 한국어로 답변해주세요: {question}"
            answer = self.llm.invoke(prompt)
            return answer.content if hasattr(answer, 'content') else str(answer)
        except Exception as e:
            print(f"DocumentRAGAgent.ask() 실행 중 오류 발생: {e}")
            return "답변을 생성하는 동안 오류가 발생했습니다."

if __name__ == "__main__":
    """
    이 스크립트를 직접 실행하면 DocumentRAGAgent 클래스의 기능을 테스트할 수 있습니다.
    """
    print("--- DocumentRAGAgent 직접 실행 테스트 ---")
    
    try:
        # 1. 에이전트 초기화 (이 과정에서 문서 동기화가 자동으로 수행됩니다)
        doc_agent = DocumentRAGAgent(index_name="carbon-multiagent")
        
        # 2. RAG Q&A 테스트
        if doc_agent.rag_chain:
            print("\n--- RAG Q&A 테스트 시작 ---")
            test_question = "온실가스 배출량 산정을 위한 자료를 제출하지 아니하거나 거짓으로 제출한 경우 과태료는?"
            print(f"\n[Question]: {test_question}\n")
            
            start_time = time.time()
            answer = doc_agent.ask(test_question)
            end_time = time.time()
            
            print(f"[Answer]:\n{answer}")
            print(f"\n(답변 생성 시간: {end_time - start_time:.2f}초)")
        else:
            print("\n테스트를 진행할 수 없습니다. RAG 체인이 성공적으로 생성되지 않았습니다.")

    except Exception as e:
        print(f"\n테스트 스크립트 실행 중 오류 발생: {e}") 