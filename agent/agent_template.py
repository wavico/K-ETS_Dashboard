import os
import sys
import json
from langchain_upstage import ChatUpstage
from langchain_core.messages import HumanMessage, SystemMessage
from dotenv import load_dotenv
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

# --- LLM 라이브러리 임포트 ---
# 사용 가능한 LLM을 동적으로 확인하고 임포트합니다.
try:
    from langchain_upstage import ChatUpstage
    UPSTAGE_AVAILABLE = True
except ImportError:
    UPSTAGE_AVAILABLE = False

try:
    from langchain_openai import ChatOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# OpenAI API Key 로딩
load_dotenv()

# 1. Pydantic 모델로 원하는 JSON 출력 구조를 정의합니다.
class OutlineNode(BaseModel):
    """목차의 단일 노드. 재귀적으로 자식 노드를 가질 수 있음"""
    title: str = Field(description="장 또는 절의 제목")
    children: Optional[List['OutlineNode']] = Field(None, description="하위 목차 노드들의 리스트")

class StructuredOutline(BaseModel):
    """보고서의 전체 구조화된 목차를 정의하는 최상위 데이터 모델"""
    outline: List[OutlineNode] = Field(description="최상위 챕터 노드들의 리스트")

# 2. 에이전트 클래스 정의
class ReportTemplateAgent:
    """
    사용자가 입력한 주제를 기반으로 보고서 템플릿(뼈대)과
    구조화된 목차(JSON)를 생성하는 에이전트 클래스
    """
    def __init__(self):
        """
        에이전트를 초기화하고 사용 가능한 API 키에 따라 LLM 클라이언트를 설정합니다.
        .env 파일에서 UPSTAGE_API_KEY와 OPENAI_API_KEY를 순차적으로 탐색합니다.
        """
        upstage_api_key = os.getenv("UPSTAGE_API_KEY")
        openai_api_key = os.getenv("OPENAI_API_KEY")

        if UPSTAGE_AVAILABLE and upstage_api_key:
            self.client = ChatUpstage(api_key=upstage_api_key, model="solar-mini", temperature=0.4)
            print("✅ ReportTemplateAgent: Upstage LLM (solar-mini)을 사용합니다.")
        elif OPENAI_AVAILABLE and openai_api_key:
            self.client = ChatOpenAI(api_key=openai_api_key, model="gpt-4.1-nano", temperature=0.4)
            print("✅ ReportTemplateAgent: OpenAI LLM (gpt-4.1-nano)을 사용합니다.")
        else:
            raise ValueError("API 키가 설정되지 않았습니다. .env 파일에서 UPSTAGE_API_KEY 또는 OPENAI_API_KEY를 설정해주세요.")

    def generate_report_template(self, topic: str) -> str:
        """
        주어진 주제에 대한 보고서의 뼈대(템플릿)를 텍스트 형식으로 생성

        이 함수는 LLM을 호출하여 주제에 맞는 서론, 본론, 결론을 포함하는
        전문적인 보고서 목차를 생성

        Args:
            topic (str): 생성할 보고서의 주제

        Returns:
            str: 보고서의 뼈대가 되는 템플릿 텍스트
                 오류 발생 시 빈 문자열을 반환

        Example:
            >>> agent = ReportTemplateAgent()
            >>> topic = "국내 탄소 배출 현황"
            >>> template = agent.generate_report_template(topic)
            >>> print(template)
            제 1장 서론
            1.1. 연구의 배경 및 필요성
            ...
        """
        prompt = f"""
        다음 주제에 대한 전문적인 보고서의 목차(뼈대)를 생성해 주세요: '{topic}'

        요구사항:
        - 일반적인 보고서 형식에 따라 '서론', '본론', '결론'을 포함해야 합니다.
        - 각 장(Chapter)과 절(Section)은 명확하게 번호로 구분되어야 합니다 (예: 1., 1.1., 2.1.1.).
        - 내용은 '{topic}'이라는 주제에 맞춰 전문적이고 논리적인 흐름을 가져야 합니다.

        출력 예시:
        ---
        제 1장 서론
        1.1. 연구의 배경 및 필요성
        1.2. 연구의 목적 및 범위

        제 2장 국내 탄소 배출 현황 분석
        2.1. 연도별 총배출량 변화 추이
        ...
        ---
        """
        try:
            # 1. 메시지를 LangChain의 Message 객체로 만들기 (dict가 아님)
            messages = [
                SystemMessage(content="당신은 전문적인 보고서의 목차를 구조적으로 작성하는 AI입니다."),
                HumanMessage(content=prompt)
            ]
            
            # 2. 표준 'invoke' 메소드를 사용
            #    model, temperature 등은 여기서도 지정가능한데, 나는 앞에서 지정해놓고 씀
            response = self.client.invoke(
                messages
            )

            # 3. LangChain의 AIMessage 객체에서 .content 속성으로 결과에 접근
            template_text = response.content.strip()
            return template_text

        except Exception as e:
            print(f"보고서 템플릿 생성 중 오류가 발생했습니다: {e}")
            return ""

    def generate_structured_outline(self, template_text: str) -> Dict[str, Any]:
        """
        텍스트 형식의 보고서 템플릿을 구조화된 JSON 객체로 변환

        (Docstring은 기존과 동일하므로 생략)
        """
        # 프롬프트는 기존 로직을 그대로 사용합니다.
        prompt = f"""
        다음 텍스트로 작성된 보고서 목차를 기계가 처리하기 용이한 JSON 형식으로 변환해 주세요.

        요구사항:
        1.  최상위 키는 'outline' 이어야 하며, 그 값은 챕터 객체들의 리스트입니다.
        2.  각 챕터 객체는 'title' (문자열)과 'children' (하위 섹션 객체들의 리스트) 키를 가져야 합니다.
        3.  각 하위 섹션 객체는 'title' (문자열) 키를 가지며, 필요한 경우 재귀적으로 'children' 키를 가질 수 있습니다.
        4.  계층의 깊이에는 제한이 없습니다.

        입력 목차 텍스트:
        ---
        {template_text}
        ---

        위 요구사항에 따라 JSON 형식으로만 출력해주세요. 다른 설명은 포함하지 마세요.
        """
        
        try:
            # 4. LangChain의 `with_structured_output`을 사용하여 JSON 출력을 강제합니다.
            #    Pydantic 모델(StructuredOutline)을 넘겨주어 원하는 출력 구조를 알려줍니다.
            if not hasattr(self.client, 'with_structured_output'):
                raise NotImplementedError("현재 LLM 클라이언트는 'with_structured_output'을 지원하지 않습니다.")

            structured_llm = self.client.with_structured_output(StructuredOutline)

            # 5. 메시지를 LangChain의 표준 객체로 구성합니다.
            messages = [
                SystemMessage(content="당신은 텍스트 형식의 목차를 구조화된 JSON으로 변환하는, 정확하고 논리적인 AI입니다."),
                HumanMessage(content=prompt)
            ]

            # 6. 바인딩된 LLM을 `invoke` 메소드로 호출합니다.
            #    temperature 등 추가 파라미터는 여기서 지정할 수 있습니다.
            response_obj = structured_llm.invoke(messages, temperature=0.1)

            # 7. 결과는 이미 파싱된 Pydantic 객체입니다.
            #    json.loads()가 필요 없으며, .dict() 메소드로 Python 딕셔너리로 변환합니다.
            return response_obj.dict()

        except Exception as e:
            print(f"구조화된 목차 생성 중 오류가 발생했습니다: {e}")
            return {}


if __name__ == '__main__':
    """
    ReportTemplateAgent 클래스의 기능을 테스트
    """
    try:
        # --- 프로젝트 루트를 sys.path에 추가 ---
        # 이 스크립트가 다른 모듈을 올바르게 임포트할 수 있도록 프로젝트의 루트 디렉토리를 시스템 경로에 추가합니다.
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if project_root not in sys.path:
            sys.path.insert(0, project_root)
    except Exception as e:
        print(f"경로 추가 중 오류 발생: {e}")
        project_root = "."


    print("--- ReportTemplateAgent 기능 테스트 시작 ---")
    
    try:
        agent = ReportTemplateAgent()
        
        # 1. 보고서 템플릿 생성 기능 테스트
        test_topic = "국내 탄소 배출 현황 및 감축 전략"
        print(f"\n[1] 주제: '{test_topic}'에 대한 보고서 템플릿 생성")
        report_template = agent.generate_report_template(test_topic)
        
        if report_template:
            print("--- 생성된 템플릿 ---")
            print(report_template)
            print("-" * 50)
            
            # 2. 구조화된 목차(JSON) 생성 기능 테스트
            print("\n[2] 생성된 템플릿을 구조화된 JSON 목차로 변환")
            outline_json = agent.generate_structured_outline(report_template)
            
            if outline_json:
                # JSON을 보기 좋게 출력
                print("--- 생성된 JSON 목차 ---")
                print(json.dumps(outline_json, indent=4, ensure_ascii=False))
                print("-" * 50)

                # 3. 결과물을 파일로 저장
                try:
                    # 'template' 디렉토리가 있는지 확인하고 없으면 생성
                    output_dir = os.path.join(project_root, 'template')
                    os.makedirs(output_dir, exist_ok=True)
                    
                    output_path = os.path.join(output_dir, "outline.json")
                    with open(output_path, "w", encoding="utf-8") as f:
                        json.dump(outline_json, f, indent=4, ensure_ascii=False)
                    print(f"\n[3] ✅ 테스트 결과가 '{output_path}' 파일로 성공적으로 저장되었습니다.")
                except Exception as e:
                    print(f"\n[3] ❌ 파일 저장 중 오류 발생: {e}")
            else:
                print("\n[2] ❌ 구조화된 목차 생성에 실패했습니다.")
        else:
            print("\n[1] ❌ 보고서 템플릿 생성에 실패했습니다.")
            
    except ValueError as ve:
        print(f"\n❌ 에이전트 초기화 오류: {ve}")
    except Exception as e:
        print(f"\n❌ 테스트 실행 중 예기치 않은 오류가 발생했습니다: {e}")

    print("\n--- 테스트 종료 ---") 