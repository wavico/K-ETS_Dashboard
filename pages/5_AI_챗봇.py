"""
AI 챗봇 페이지
탄소 배출 데이터 분석을 위한 AI 챗봇 인터페이스
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import sys
import os
from dotenv import load_dotenv

# .env 파일 로드 시도
try:
    load_dotenv()
    # .env 파일이 없거나 로드에 실패한 경우 경고 메시지 출력
    if not os.getenv('UPSTAGE_API_KEY'):
        print("⚠️ UPSTAGE_API_KEY가 설정되지 않았습니다. env.example 파일을 참고하여 .env 파일을 생성해주세요.")
except Exception as e:
    st.error(f"환경변수 로드 중 오류: {e}")
    st.error("⚠️ .env 파일을 확인해주세요. env.example 파일을 참고하여 .env 파일을 생성할 수 있습니다.")

# 상위 디렉토리의 모듈 import를 위한 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 향상된 에이전트 import
try:
    from agent.enhanced_carbon_rag_agent import EnhancedCarbonRAGAgent
    AGENT_AVAILABLE = True
except ImportError as e:
    st.error(f"EnhancedCarbonRAGAgent 모듈을 불러올 수 없습니다: {e}")
    AGENT_AVAILABLE = False

# 페이지 설정은 main.py에서 처리됨

# CSS 스타일
st.markdown("""
<style>
    .main-header {
        font-size: 28px;
        font-weight: bold;
        background: linear-gradient(90deg, #1f77b4, #ff7f0e, #2ca02c);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 30px;
    }
    .chat-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 15px;
        color: white;
        margin: 20px 0;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    .chat-message {
        background: rgba(255,255,255,0.1);
        padding: 12px;
        border-radius: 8px;
        margin: 10px 0;
    }
    .user-message {
        background: linear-gradient(135deg, #74b9ff 0%, #0984e3 100%);
        margin-left: 10%;
        margin-right: 5%;
    }
    .assistant-message {
        background: linear-gradient(135deg, #00b894 0%, #00a085 100%);
        margin-left: 5%;
        margin-right: 10%;
    }
    .data-info-card {
        background: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        margin: 15px 0;
        border-left: 4px solid #1f77b4;
    }
    .example-queries {
        background: linear-gradient(135deg, #fd79a8 0%, #e84393 100%);
        padding: 20px;
        border-radius: 15px;
        color: white;
        margin: 15px 0;
    }
    .stButton > button {
        width: 100%;
        margin: 5px 0;
        border-radius: 20px;
        border: none;
        padding: 10px;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    
    /* 그래프 크기 제어 */
    .stPlotlyChart, .element-container:has(.stPlotlyChart) {
        max-width: 800px !important;
        margin: 0 auto !important;
    }
    
    /* matplotlib 그래프 크기 제어 */
    .stPlotlyChart > div, .element-container > div > div > div > img {
        max-width: 800px !important;
        height: auto !important;
        margin: 0 auto !important;
    }
</style>
""", unsafe_allow_html=True)

# 세션 상태 초기화
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'agent' not in st.session_state:
    st.session_state.agent = None

# 타이틀
st.markdown('<h1 class="main-header">🤖 AI 챗봇 - 탄소 데이터 분석</h1>', unsafe_allow_html=True)

# 에이전트 초기화
@st.cache_resource
def load_agent():
    """EnhancedCarbonRAGAgent 로드 (캐시 사용)"""
    if not AGENT_AVAILABLE:
        return None
    return EnhancedCarbonRAGAgent(data_folder="data")

# 에이전트 로드
if AGENT_AVAILABLE:
    try:
        with st.spinner("🔄 AI 에이전트를 초기화하고 있습니다..."):
            agent = load_agent()
            if agent and agent.llm:
                st.success("✅ AI 에이전트가 성공적으로 초기화되었습니다!")
                st.session_state.agent = agent
            else:
                st.error("❌ AI 에이전트 초기화에 실패했습니다.")
                st.stop()
    except Exception as e:
        st.error(f"❌ 에이전트 초기화 중 오류 발생: {e}")
        st.stop()
else:
    st.error("❌ EnhancedCarbonRAGAgent를 사용할 수 없습니다.")
    st.stop()

# 데이터 정보 표시
if st.session_state.agent:
    st.markdown("""
    <div class="data-info-card">
        <h3>📊 데이터 정보</h3>
    </div>
    """, unsafe_allow_html=True)
    
    data_info = st.session_state.agent.get_available_data_info()
    st.markdown(data_info)

# 예시 질문들
st.markdown("""
<div class="example-queries">
    <h3>💡 빠른 질문 예시</h3>
    <p>아래 버튼을 클릭하여 빠르게 데이터를 분석해보세요!</p>
</div>
""", unsafe_allow_html=True)

if st.session_state.agent:
    sample_questions = st.session_state.agent.get_sample_questions()
    
    # 예시 질문 버튼들 (3x2 그리드)
    col1, col2, col3 = st.columns(3)
    
    for i, question in enumerate(sample_questions):
        col = [col1, col2, col3][i % 3]
        with col:
            if st.button(f"💬 {question}", key=f"sample_{i}"):
                # 질문 처리
                with st.spinner("🤔 AI가 분석하고 있습니다..."):
                    try:
                        response, visualization, table_data, figure_obj = st.session_state.agent.ask(question)
                        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        st.session_state.chat_history.append((question, response, timestamp, visualization, table_data, figure_obj))
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ 오류가 발생했습니다: {e}")

# 채팅 인터페이스
st.markdown("""
<div class="chat-container">
    <h3>💬 AI와 대화하기</h3>
    <p>탄소 배출 데이터에 대해 궁금한 것을 자유롭게 물어보세요!</p>
</div>
""", unsafe_allow_html=True)

# 채팅 히스토리 표시
for chat_item in st.session_state.chat_history:
    # 다양한 형식 지원
    if len(chat_item) == 3:
        user_msg, assistant_msg, timestamp = chat_item
        visualization = None
        table_data = None
        figure_obj = None
    elif len(chat_item) == 4:
        user_msg, assistant_msg, timestamp, visualization = chat_item
        table_data = None
        figure_obj = None
    elif len(chat_item) == 5:
        user_msg, assistant_msg, timestamp, visualization, table_data = chat_item
        figure_obj = None
    else:
        user_msg, assistant_msg, timestamp, visualization, table_data, figure_obj = chat_item
    
    st.markdown(f"""
    <div class="chat-message user-message">
        <strong>🙋‍♂️ 사용자 ({timestamp}):</strong><br>
        {user_msg}
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"""
    <div class="chat-message assistant-message">
        <strong>🤖 AI 어시스턴트:</strong><br>
        {assistant_msg}
    </div>
    """, unsafe_allow_html=True)
    
    # 테이블이 생성된 경우 표시
    if table_data is not None:
        st.markdown("**📊 분석 결과 테이블:**")
        st.dataframe(table_data, use_container_width=True)
    
    # 그래프가 생성된 경우 표시
    if visualization == "plot_generated":
        try:
            # 방법 1: 컬럼과 직접 표시 (기본)
            col1, col2, col3 = st.columns([1.5, 1, 1.5])
            
            with col2:  # 중앙 컬럼에만 그래프 표시
                st.markdown('<div style="max-width: 400px; margin: 0 auto;">', unsafe_allow_html=True)
                
                # figure 객체가 있으면 직접 사용
                if figure_obj is not None:
                    st.pyplot(figure_obj, use_container_width=False)
                # 없으면 기존 방식 사용
                elif plt.get_fignums():
                    st.pyplot(plt.gcf(), use_container_width=False)
                
                st.markdown('</div>', unsafe_allow_html=True)
            
            # 방법 2: 이미지로 저장 후 크기 제어 (주석 처리 - 필요시 활성화)
            # import io
            # import base64
            # 
            # if figure_obj is not None:
            #     # 그래프를 이미지로 저장
            #     buf = io.BytesIO()
            #     figure_obj.savefig(buf, format='png', dpi=80, bbox_inches='tight')
            #     buf.seek(0)
            #     
            #     # 중앙 정렬로 이미지 표시
            #     col1, col2, col3 = st.columns([2, 1, 2])
            #     with col2:
            #         st.image(buf, width=400)  # 고정 너비 400px
            
            # 메모리 정리
            import matplotlib.pyplot as plt
            plt.close('all')
        except Exception as e:
            st.write(f"그래프 표시 중 오류: {e}")

# 사용자 입력
st.markdown("### 💭 새로운 질문하기")

# 엔터키 처리를 위한 폼 사용
with st.form(key='question_form', clear_on_submit=True):
    user_input = st.text_input(
        "질문을 입력하세요:",
        placeholder="예: 2021년과 2022년의 배출량 차이는 얼마나 되나요?",
        key="user_input_form"
    )
    
    col1, col2 = st.columns([3, 1])
    with col1:
        submit_button = st.form_submit_button("🚀 질문하기", type="primary", use_container_width=True)
    with col2:
        clear_button = st.form_submit_button("🗑️ 채팅 지우기", use_container_width=True)

# 질문 처리
if submit_button and user_input and st.session_state.agent:
    with st.spinner("🤔 AI가 분석하고 있습니다..."):
        try:
            response, visualization, table_data, figure_obj = st.session_state.agent.ask(user_input)
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            st.session_state.chat_history.append((user_input, response, timestamp, visualization, table_data, figure_obj))
            st.rerun()
        except Exception as e:
            st.error(f"❌ 오류가 발생했습니다: {e}")
elif submit_button and not user_input:
    st.warning("질문을 입력해주세요.")

# 채팅 지우기 처리
if clear_button:
    st.session_state.chat_history = []
    st.rerun()

# 도움말
with st.expander("❓ 사용법 도움말"):
    st.markdown("""
    ### 🎯 효과적인 질문 방법
    
    **✅ 좋은 질문 예시:**
    - "2021년 총 배출량은 얼마인가요?"
    - "연도별 배출량 변화를 그래프로 보여주세요"
    - "가장 배출량이 많은 분야는 무엇인가요?"
    - "데이터의 기본 통계를 알려주세요"
    
    **❌ 피해야 할 질문:**
    - 너무 모호한 질문 ("이거 어때?")
    - 데이터에 없는 정보 요청
    - 여러 질문을 한 번에 물어보기
    
    **💡 팁:**
    - 구체적인 연도나 분야를 명시하세요
    - 그래프나 차트가 필요하면 명시적으로 요청하세요
    - 한 번에 하나의 질문만 하세요
    """) 