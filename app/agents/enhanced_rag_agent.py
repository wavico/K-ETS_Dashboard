"""
FastAPI용 향상된 탄소 데이터 분석 RAG 에이전트
"""

import os
import io
import sys
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import seaborn as sns
from pathlib import Path
from typing import Tuple, Optional, Dict, Any, List
from dotenv import load_dotenv
from matplotlib.ticker import FuncFormatter
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

# FastAPI 관련 imports
from app.agents.base_agent import BaseAgent
from app.models.agent_response import AgentResponse, VisualizationData
from app.services.document_service import DocumentRAGAgent

# LangChain imports
try:
    from langchain_upstage import ChatUpstage
    UPSTAGE_AVAILABLE = True
except ImportError:
    UPSTAGE_AVAILABLE = False
    ChatUpstage = None

try:
    from langchain_openai import ChatOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    ChatOpenAI = None

# 환경변수 로드
load_dotenv()

try:
    from app.prompts.code_generation import code_gen_prompt_template
    from app.prompts.interpretation import interpretation_prompt_template
except ImportError:
    # 프롬프트 템플릿 기본값
    code_gen_prompt_template = None
    interpretation_prompt_template = None

class EnhancedCarbonRAGAgent(BaseAgent):
    """향상된 탄소 데이터 분석 RAG 에이전트"""
    
    def __init__(self, data_folder: str = "data"):
        """
        Args:
            data_folder: CSV 파일들이 있는 폴더 경로
        """
        super().__init__("enhanced_rag")
        
        self.data_folder = Path(data_folder)
        self.df = None
        self.llm = None
        self.code_generation_chain = None
        self.doc_agent = None
        
        self._setup_korean_font()
        self._load_data()
        self._setup_llms_and_chains()

        # DocumentRAGAgent 초기화
        try:
            self.doc_agent = DocumentRAGAgent()
            print("DocumentRAGAgent initialization successful")
        except Exception as e:
            print(f"DocumentRAGAgent initialization failed: {e}")
            self.doc_agent = None
    
    async def process(self, message: str, context: Dict[str, Any]) -> AgentResponse:
        """메시지 처리"""
        try:
            # RAG 에이전트로 처리
            response_text, visualization = self.ask(message)
            
            # 시각화 데이터 변환
            visualizations = []
            if visualization:
                # Plotly 차트를 VisualizationData 형식으로 변환
                viz_data = VisualizationData(
                    chart_type="plotly",
                    data=visualization.to_dict() if hasattr(visualization, 'to_dict') else {},
                    title="데이터 분석 결과",
                    description="탄소 데이터 분석 시각화"
                )
                visualizations.append(viz_data)
            
            return AgentResponse(
                message=response_text,
                agent_type=self.agent_type,
                data={"query": message, "context": context},
                visualizations=visualizations
            )
            
        except Exception as e:
            return AgentResponse(
                message=f"분석 중 오류가 발생했습니다: {str(e)}",
                agent_type=self.agent_type
            )
    
    async def analyze_dashboard_section(self, dashboard_state: Dict) -> Dict[str, Any]:
        """대시보드 섹션 분석"""
        try:
            # 데이터 품질 분석
            data_quality = await self._assess_data_quality()
            
            # 추천사항 생성
            recommendations = await self._generate_recommendations(data_quality)
            
            return {
                "data_quality": data_quality,
                "recommendations": recommendations,
                "insights": ["데이터 분석 완료", "시각화 생성 가능"]
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    async def _assess_data_quality(self) -> Dict[str, Any]:
        """데이터 품질 평가"""
        if self.df is None:
            return {"error": "데이터가 로드되지 않았습니다"}
        
        return {
            "completeness": (1 - self.df.isnull().sum().sum() / (self.df.shape[0] * self.df.shape[1])),
            "total_rows": len(self.df),
            "total_columns": len(self.df.columns),
            "data_types": self.df.dtypes.to_dict()
        }
    
    async def _generate_recommendations(self, data_quality: Dict) -> List[str]:
        """추천사항 생성"""
        recommendations = []
        
        if data_quality.get("completeness", 0) < 0.95:
            recommendations.append("데이터 품질 개선이 필요합니다")
        
        recommendations.extend([
            "정기적인 데이터 업데이트 권장",
            "추가 데이터 소스 연계 검토",
            "데이터 검증 프로세스 강화"
        ])
        
        return recommendations
    
    def _setup_korean_font(self):
        """한글 폰트 설정"""
        try:
            # Windows 한글 폰트 설정
            font_paths = [
                'C:/Windows/Fonts/malgun.ttf',  # 맑은 고딕
                'C:/Windows/Fonts/gulim.ttc',   # 굴림
                'C:/Windows/Fonts/batang.ttc'   # 바탕
            ]
            
            for font_path in font_paths:
                if os.path.exists(font_path):
                    font_prop = fm.FontProperties(fname=font_path)
                    plt.rcParams['font.family'] = font_prop.get_name()
                    plt.rcParams['axes.unicode_minus'] = False
                    # Seaborn 스타일 설정
                    sns.set_style("whitegrid")
                    sns.set_palette("husl")
                    print(f"Korean font setup success: {font_prop.get_name()}")
                    break
        except Exception as e:
            print(f"Korean font setup failed: {e}")
    
    def _load_data(self):
        """CSV 파일들을 로드하여 통합 DataFrame 생성"""
        try:
            dataframes = []
            
            # 주요 CSV 파일들 로드
            csv_files = [
                "환경부 온실가스종합정보센터_국가 온실가스 인벤토리 배출량_20250103.csv",
                "배출권_거래데이터.csv",
                "01. 3차_사전할당_20250613090824.csv",
                "한국에너지공단_산업부문 에너지사용 및 온실가스배출량 통계_20231231.csv"
            ]
            
            for filename in csv_files:
                filepath = self.data_folder / filename
                if filepath.exists():
                    # 다양한 인코딩으로 시도
                    for encoding in ['cp949', 'euc-kr', 'utf-8', 'utf-8-sig']:
                        try:
                            df = pd.read_csv(filepath, encoding=encoding, low_memory=False)
                            df['데이터소스'] = filename
                            dataframes.append(df)
                            print(f"Loaded successfully: {filename} ({df.shape})")
                            break
                        except UnicodeDecodeError:
                            continue
                    else:
                        print(f"Failed to load: {filename}")
            
            # 통합 DataFrame 생성
            if dataframes:
                self.df = pd.concat(dataframes, ignore_index=True, sort=False)
                print(f"Integrated data: {self.df.shape}")
                
                # 데이터 타입 분석 및 최적화
                self._analyze_and_optimize_data()
            else:
                # 테스트 데이터 생성
                years = list(range(1990, 2023))
                emissions = [500000 + i*10000 + (i%5)*5000 for i in range(len(years))]
                self.df = pd.DataFrame({
                    '연도': years,
                    '총배출량': emissions,
                    '에너지': [e*0.7 for e in emissions],
                    '산업공정': [e*0.15 for e in emissions],
                    '농업': [e*0.1 for e in emissions],
                    '폐기물': [e*0.05 for e in emissions],
                    '데이터소스': ['테스트'] * len(years)
                })
                print("⚠️ 테스트 데이터로 초기화됨")
                self._analyze_and_optimize_data()
                
        except Exception as e:
            print(f"Data loading error: {e}")
            # 빈 DataFrame으로 초기화
            self.df = pd.DataFrame()
    
    def _analyze_and_optimize_data(self):
        """데이터 타입 분석 및 최적화"""
        if self.df is None or self.df.empty:
            return
        
        # 연도 관련 컬럼 찾기
        year_patterns = ['연도', 'year', '년도', '년', 'YEAR', 'Year']
        self.year_columns = []
        self.column_types = {}
        
        for col in self.df.columns:
            col_lower = str(col).lower()
            
            # 연도 컬럼 감지
            if any(pattern.lower() in col_lower for pattern in year_patterns):
                self.year_columns.append(col)
                
                # 연도 컬럼의 데이터 타입 확인 및 변환 시도
                try:
                    # 샘플 값으로 타입 확인
                    sample_values = self.df[col].dropna().head(10)
                    if len(sample_values) > 0:
                        first_val = sample_values.iloc[0]
                        
                        # 문자열인 경우 숫자로 변환 시도
                        if isinstance(first_val, str):
                            # '2017년' -> '2017' 변환
                            cleaned_values = sample_values.astype(str).str.replace('년', '').str.strip()
                            if cleaned_values.str.isdigit().all():
                                self.df[col] = self.df[col].astype(str).str.replace('년', '').str.strip()
                                self.df[col] = pd.to_numeric(self.df[col], errors='coerce')
                                # 소수점 제거하여 정수로 변환
                                self.df[col] = self.df[col].astype('Int64')
                                self.column_types[col] = 'numeric_year'
                                print(f"Year column '{col}' converted to integer")
                            else:
                                self.column_types[col] = 'string_year'
                                print(f"Year column '{col}' kept as string")
                        else:
                            # 숫자 타입인 경우 소수점 제거
                            try:
                                # float 타입인 경우 정수로 변환
                                if self.df[col].dtype in ['float64', 'float32']:
                                    self.df[col] = self.df[col].astype('Int64')
                                    print(f"Year column '{col}' converted to integer by removing decimal")
                                else:
                                    print(f"Year column '{col}' already integer type")
                                self.column_types[col] = 'numeric_year'
                            except Exception as conv_error:
                                print(f"Year column '{col}' integer conversion failed: {conv_error}")
                                self.column_types[col] = 'numeric_year'
                            
                except Exception as e:
                    self.column_types[col] = 'unknown_year'
                    print(f"Year column '{col}' type analysis failed: {e}")
            
            # 기타 컬럼 타입 저장
            elif col not in self.column_types:
                dtype = str(self.df[col].dtype)
                self.column_types[col] = dtype
        
        print(f"Year columns found: {self.year_columns}")
        print(f"Column type info: {len(self.column_types)} columns analyzed")
    
    def _setup_llms_and_chains(self):
        """사용 가능한 API 키에 따라 LLM 및 모든 LCEL 체인을 초기화하고 설정합니다."""
        try:
            from prompts.code_generation import code_gen_prompt_template
        except ImportError:
            # Fallback to default prompt if prompts module is not available
            from langchain_core.prompts import PromptTemplate
            code_gen_prompt_template = PromptTemplate.from_template(
                "You are a Python data analysis expert. Generate Python code to analyze the given data.\n"
                "Data columns: {columns}\n"
                "User request: {query}\n"
                "Generate only the Python code without explanations:"
            )
        
        try:
            # 1. API 키 및 vLLM 설정 확인
            use_vllm = os.getenv("USE_VLLM", "true").lower() == "true"
            vllm_base_url = os.getenv("VLLM_BASE_URL", "http://localhost:8000/v1")
            vllm_model_name = os.getenv("VLLM_MODEL_NAME", "gpt-4-turbo")
            upstage_api_key = os.getenv("UPSTAGE_API_KEY")
            openai_api_key = os.getenv("OPENAI_API_KEY")

            # 2. 기본 LLM 설정 (vLLM 우선)
            if use_vllm and OPENAI_AVAILABLE:
                self.llm = ChatOpenAI(
                    base_url=vllm_base_url,
                    api_key="EMPTY",
                    model=vllm_model_name,
                    temperature=0
                )
                print(f"EnhancedCarbonRAGAgent: Using vLLM ({vllm_base_url})")
            elif UPSTAGE_AVAILABLE and upstage_api_key:
                self.llm = ChatUpstage(api_key=upstage_api_key, model="solar-mini", temperature=0)
                print("EnhancedCarbonRAGAgent: Using Upstage LLM (solar-mini)")
            elif OPENAI_AVAILABLE and openai_api_key:
                self.llm = ChatOpenAI(api_key=openai_api_key, model="gpt-4.1-nano", temperature=0)
                print("EnhancedCarbonRAGAgent: Using OpenAI LLM (gpt-4.1-nano)")
            else:
                self.llm = None
                print("⚠️ 경고: 사용 가능한 API 키가 없거나 vLLM 서버가 실행되지 않았습니다. .env 파일을 확인해주세요.")

            # 3. 코드 생성(Code Generation) 체인 설정 (LLM이 성공적으로 초기화된 경우에만)
            if self.llm:
                self.code_generation_chain = code_gen_prompt_template | self.llm | StrOutputParser()
                print("Code generation chain initialization complete")
            else:
                self.code_generation_chain = None
                print("⚠️ 코드 생성 체인을 초기화할 수 없습니다 (LLM 사용 불가).")

        except Exception as e:
            print(f"LLM and chain initialization failed: {e}")
            self.llm = None
            self.code_generation_chain = None
            
    def _generate_code(self, question: str) -> str:
        """질문을 분석하여 Python 코드를 생성 (LCEL 체인 사용)"""
        if not self.code_generation_chain:
            print("⚠️ 코드 생성 체인이 없어 코드 생성을 건너뜁니다.")
            return None
            
        # 프롬프트에 필요한 정보 준비
        columns_info = ', '.join(self.df.columns[:10].tolist()) if self.df is not None else ''
        
        # 데이터소스 정보 생성
        if self.df is not None and '데이터소스' in self.df.columns:
            datasources = self.df['데이터소스'].unique()[:5]
            datasource_info = f"- 데이터소스: {', '.join(datasources)}"
        else:
            datasource_info = "- 데이터소스: 통합 탄소 배출량 데이터"
            
        # 연도 정보 생성
        if self.df is not None and any(col in self.df.columns for col in self.year_columns):
            # 사용 가능한 첫 번째 연도 컬럼을 사용
            year_col_to_use = next((col for col in self.year_columns if col in self.df.columns), None)
            if year_col_to_use:
                try:
                    # 데이터 타입이 숫자일 때만 min/max를 안전하게 계산
                    if pd.api.types.is_numeric_dtype(self.df[year_col_to_use]):
                        years = self.df[year_col_to_use].dropna()
                        if not years.empty:
                            min_year, max_year = int(years.min()), int(years.max())
                            year_info = f"- 연도 범위: {min_year}년 ~ {max_year}년"
                        else:
                             year_info = "- 연도 정보: 연도 데이터가 비어있음"
                    else:
                        # 숫자가 아닌 경우, 고유값 몇 개를 보여줌
                        unique_years = self.df[year_col_to_use].dropna().unique()[:5]
                        year_info = f"- 연도 정보 (샘플): {', '.join(map(str, unique_years))}"

                except Exception as e:
                    year_info = f"- 연도 정보 분석 실패: {e}"
            else:
                year_info = "- 연도 정보: 해당 컬럼 없음"
        else:
            year_info = "- 연도 정보: 연도 데이터 없음"

        sample_data = self.df.head(3).to_string() if self.df is not None else "데이터 없음"
        
        try:
            # LCEL 체인 호출
            code = self.code_generation_chain.invoke({
                "question": question,
                "data_shape": self.df.shape,
                "columns_info": columns_info,
                "datasource_info": datasource_info,
                "year_info": year_info,
                "sample_data": sample_data
            })
            
            # 코드 블록 추출 (수정된 로직)
            if "```python" in code:
                # ```python으로 시작하는 코드 블록 추출
                code = code.split("```python", 1)[1].split("```", 1)[0]
            elif "```" in code:
                # 일반 코드 블록의 경우
                parts = code.split("```")
                if len(parts) >= 3:
                    code = parts[1]  # 첫 번째 코드 블록 추출
                # 가끔 'python'이 맨 앞에 붙는 경우를 대비해 제거
                if code.lstrip().startswith('python'):
                    code = code.lstrip()[6:]
                else:
                    # 코드 블록이 제대로 감싸지지 않은 경우
                    code = code.split("```")[1] if len(parts) >= 2 else code

            # 이제 code는 확실히 문자열이므로 .strip()이 안전하게 작동합니다.
            return code.strip()
    
        except Exception as e:
            print(f"Code generation failed: {e}")
            return None
        
    def _execute_code(self, code: str) -> Tuple[str, bool, Optional[pd.DataFrame], Optional[object], Dict[str, Any]]:
        """안전하게 코드 실행하고, 실행 컨텍스트(namespace)도 함께 반환"""
        if not code:
            return "코드를 생성할 수 없습니다.", False, None, None, {}
        
        try:
            # 코드 사전 검증 및 정리
            code = code.strip()
            
            # 위험한 코드 패턴 검사
            dangerous_patterns = [
                'import os', 'import sys', 'exec(', 'eval(', 
                'open(', '__import__', 'globals()', 'locals()'
            ]
            
            for pattern in dangerous_patterns:
                if pattern in code:
                    return f"보안상 위험한 코드가 감지되었습니다: {pattern}", False, None, None, {}
            
            # 안전한 실행 환경 구성
            safe_builtins = {
                'len': len, 'str': str, 'int': int, 'float': float,
                'list': list, 'dict': dict, 'tuple': tuple,
                'range': range, 'enumerate': enumerate,
                'sum': sum, 'min': min, 'max': max,
                'abs': abs, 'round': round,
                'print': print,
                'type': type, 'isinstance': isinstance,
                'sorted': sorted, 'reversed': reversed,
                'zip': zip, 'any': any, 'all': all,
                'bool': bool, 'set': set,
                '__import__': __import__  # matplotlib 등 내부 동작에 필요
            }
            
            namespace = {
                '__builtins__': safe_builtins,
                'df': self.df,
                'pd': pd,
                'plt': plt,
                'sns': sns,
                'np': np,  # numpy 추가
                'FuncFormatter': FuncFormatter,
                'math': __import__('math'),  # 수학 함수들
                'datetime': __import__('datetime'),  # 날짜 관련
                'result': "",
                'table_result': None
            }
            
            # 실행 전 matplotlib 한글 폰트 재설정
            plt.rcParams['font.family'] = 'Malgun Gothic'
            plt.rcParams['axes.unicode_minus'] = False
            
            # 기존 그래프 정리
            plt.close('all')
            
            # stdout 캡처
            old_stdout = sys.stdout
            sys.stdout = captured_output = io.StringIO()
            
            # 그래프 생성 전 상태 확인
            figs_before = len(plt.get_fignums())
            
            # 코드 실행 (더 안전한 방식)
            try:
                exec(code, namespace)
            except NameError as ne:
                sys.stdout = old_stdout
                plt.close('all')
                return f"변수 정의 오류: {str(ne)}. 모든 변수를 사용하기 전에 정의해주세요.", False, None, None, {}
            except Exception as exec_error:
                sys.stdout = old_stdout
                plt.close('all')
                return f"코드 실행 중 오류: {str(exec_error)}", False, None, None, {}
            
            # stdout 복원
            sys.stdout = old_stdout
            
            # 그래프 생성 후 상태 확인
            figs_after = len(plt.get_fignums())
            has_plot = figs_after > figs_before
            
            # 결과 추출
            result = namespace.get('result', captured_output.getvalue())
            table_result = namespace.get('table_result', None)
            
            # table_result 타입 검증 및 정리
            if table_result is not None:
                if isinstance(table_result, str):
                    # 문자열인 경우 None으로 처리
                    table_result = None
                elif hasattr(table_result, 'shape'):
                    # DataFrame이나 numpy array인 경우 정상 처리
                    pass
                else:
                    # 기타 타입인 경우 None으로 처리
                    table_result = None
            
            # 그래프 객체 추출
            figure_obj = None
            if has_plot and plt.get_fignums():
                try:
                    # 현재 활성 figure 가져오기
                    figure_obj = plt.gcf()
                    # figure가 비어있지 않은지 확인
                    if figure_obj.get_axes():
                        print(f"Graph created: figure object extracted")
                    else:
                        figure_obj = None
                        has_plot = False
                except Exception as e:
                    print(f"Graph object extraction failed: {e}")
                    figure_obj = None
                    has_plot = False
            
            # 디버깅 정보
            if has_plot:
                print(f"Graph created: {figs_before} -> {figs_after}")
            if table_result is not None:
                print(f"Table created: {table_result.shape}")
            
            return str(result), has_plot, table_result, figure_obj, namespace
            
        except Exception as e:
            sys.stdout = old_stdout
            plt.close('all')  # 오류 시에도 그래프 정리
            return f"코드 실행 오류: {str(e)}", False, None, None, {}
    
    def ask(self, question: str, section_title: Optional[str] = None) -> Tuple[str, Optional[str], Optional[pd.DataFrame], Optional[object]]:
        """
        질문 처리의 전체 과정을 조율(Orchestrate)합니다.
        질문에 답하거나, 주어진 섹션 제목에 대한 보고서 본문을 생성합니다.

        1. 코드 생성 -> 2. 코드 실행 -> 3. 문서 기반 답변 조회 -> 4. 최종 답변 조합 및 서술형 변환
        
        Args:
            question (str): 분석을 위한 핵심 질문입니다.
            section_title (Optional[str]): None이 아닌 경우, 최종 결과를 이 제목의 보고서 섹션으로 포맷팅합니다.

        Returns:
            - 최종 답변 또는 보고서 섹션 본문 (str)
            - 'plot_generated' 또는 None (str)
            - 테이블 데이터 (pd.DataFrame)
            - 그래프 객체 (matplotlib.figure.Figure)
        """
        if not self.llm:
            return "❌ LLM이 초기화되지 않았습니다. API 키를 확인해주세요.", None, None, None
        if self.df is None or self.df.empty:
            return "❌ 데이터가 로드되지 않았습니다.", None, None, None

        try:
            # 1단계: 분석 코드 생성
            code = self._generate_code(question)
            if not code:
                return "❌ 분석 코드를 생성할 수 없습니다.", None, None, None

            # 2단계: 코드 실행하여 사실적 결과 얻기
            analytical_result, has_plot, table_result, figure_obj, namespace = self._execute_code(code)
            
            # 3단계: 최종 결과 문자열 포맷팅
            try:
                # namespace에 있는 변수들을 사용하여 문자열의 {변수} 부분을 실제 값으로 채웁니다.
                analytical_result = analytical_result.format(**namespace)
            except (KeyError, IndexError) as e:
                # 포맷팅에 실패하면 (예: result에 변수가 없는 경우) 원본 결과 사용
                print(f"ℹ️ 정보: 결과 문자열 포맷팅 스킵 ({e})")

            # 4단계: 문서 기반의 사실적 답변 생성 (DocumentRAGAgent 호출)
            document_based_answer = ""
            if self.doc_agent and self.doc_agent.rag_chain:
                print("🤔 문서 기반 답변 조회 중...")
                document_based_answer = self.doc_agent.ask(question)
            elif self.doc_agent:
                 print("⚠️ DocumentRAGAgent는 초기화되었으나 RAG 체인이 없어 문서 검색을 건너뜁니다.")
            else:
                print("⚠️ DocumentRAGAgent가 초기화되지 않아 문서 기반 답변을 생성할 수 없습니다.")

            # 5단계: 최종 답변 생성 (조건부 서술형 변환)
            if section_title:
                # 보고서 섹션 생성을 위한 프롬프트
                report_section_prompt_template = PromptTemplate.from_template(
                    """
                    당신은 데이터 분석 결과를 바탕으로 전문적인 보고서의 한 섹션을 작성하는 AI입니다.
                    아래에 제공되는 [분석 결과 요약]과 [관련 문서 정보]를 바탕으로, '{section_title}' 섹션에 들어갈 본문 내용을 서술형으로 작성해주세요.

                    - 딱딱하고 전문적인 톤을 유지하세요.
                    - "분석 결과에 따르면"과 같은 서두 대신, 자연스럽게 본문을 시작하세요.
                    - 숫자나 핵심적인 사실을 문장에 포함하여 신뢰도를 높이세요.
                    - 최종 결과물은 다른 설명 없이, 보고서 본문 내용만 포함해야 합니다.

                    [분석 결과 요약]:
                    {analytical_result}

                    [관련 문서 정보]:
                    {document_based_answer}
                    """
                )
                
                # 서술형 변환 체인 생성 및 실행
                rewriting_chain = report_section_prompt_template | self.llm | StrOutputParser()
                
                final_answer = rewriting_chain.invoke({
                    "section_title": section_title,
                    "analytical_result": analytical_result,
                    "document_based_answer": document_based_answer
                })

            else:
                # 일반 질문에 대한 답변 조합
                final_answer = f"📊 **분석 결과**\n{analytical_result}"
                if document_based_answer and "오류" not in document_based_answer and document_based_answer.strip():
                    final_answer += f"\n\n📄 **관련 문서 정보**\n{document_based_answer}"
            
            return final_answer, "plot_generated" if has_plot else None, table_result, figure_obj

        except Exception as e:
            return f"❌ 전체 프로세스에서 오류가 발생했습니다: {str(e)}", None, None, None

    def get_available_data_info(self) -> str:
        """데이터 정보 반환 (기존 인터페이스 호환성)"""
        if self.df is None or self.df.empty:
            return "데이터가 로드되지 않았습니다."
        
        info = f"""
📊 **데이터 정보**
- 총 행 수: {len(self.df):,}
- 총 열 수: {len(self.df.columns)}
- 데이터 소스: {self.df['데이터소스'].nunique() if '데이터소스' in self.df.columns else '알 수 없음'}개

**주요 컬럼:**
{', '.join(self.df.columns[:10].tolist())}
{"..." if len(self.df.columns) > 10 else ""}

**사용 가능한 질문 예시:**
- "데이터에 몇 개의 행이 있어?"
- "연도별 총 배출량 변화를 보여줘"
- "가장 배출량이 많은 연도는?"
- "배출량 데이터를 시각화해줘"
        """
        return info
    
    def get_system_status(self) -> dict:
        """시스템 상태 반환 (기존 인터페이스 호환성)"""
        return {
            "agent_initialized": self.llm is not None,
            "data_loaded": self.df is not None and not self.df.empty,
            "data_shape": self.df.shape if self.df is not None else (0, 0),
            "upstage_available": UPSTAGE_AVAILABLE,
            "api_key_set": bool(os.getenv('UPSTAGE_API_KEY'))
        }
    
    def get_sample_questions(self) -> list:
        """예시 질문들 반환"""
        return [
            "데이터에 몇 개의 행이 있어?",
            "연도별 총 배출량 변화를 그래프로 보여줘",
            "가장 배출량이 많은 연도는?",
            "에너지 부문 배출량 추이를 분석해줘",
            "배출량 데이터의 기본 통계를 보여줘",
            "최근 5년간의 배출량 추이는?"
        ]


# Add a new chain
# 관심사 분리 목적
# 해석은 실제 코드 실행 결과 -> 사실 기반의 해석 필요
# 유지보수에 이점
if __name__ == "__main__":

    # Agent 초기화
    agent = EnhancedCarbonRAGAgent()
    
    # 데이터 정보 출력
    print(agent.get_available_data_info())
    
    # 예시 질문들
    sample_questions = agent.get_sample_questions()
    print("\n💡 예시 질문들:")
    for i, q in enumerate(sample_questions, 1):
        print(f"{i}. {q}")
    
    # 대화형 모드
    print("\n🤖 탄소 데이터 분석 Agent가 준비되었습니다!")
    print("질문을 입력하세요 (종료: 'quit')")
    
    while True:
        question = input("\n❓ 질문: ")
        if question.lower() in ['quit', 'exit', '종료']:
            break

        # 보고서 섹션 생성 테스트를 위한 분기
        if question.startswith("보고서:"):
            section_title = question.replace("보고서:", "").strip()
            print(f"🤔 보고서 섹션 생성 중... (제목: {section_title})")
            # 질문은 제목과 동일하게 사용하거나, 더 구체적인 질문으로 변환 가능
            # 여기서는 간단히 제목을 질문으로 사용
            answer, _, table_result, figure_obj = agent.ask(question=section_title, section_title=section_title)
        
        else:
            print("🤔 분석 중...")
            answer, _, table_result, figure_obj = agent.ask(question)

        print(f"🤖 답변: {answer}")

        if table_result is not None:
            print("\n--- 테이블 데이터 ---")
            print(table_result)
        
        if figure_obj is not None:
            # 테스트 환경에서는 그래프를 보여주고 닫음
            print("\n(그래프가 생성되었습니다. Streamlit 환경에서는 자동으로 표시됩니다.)")
            plt.show()