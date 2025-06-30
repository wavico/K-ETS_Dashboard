"""
AI 챗봇 독립 실행 앱
iframe으로 임베드하기 위한 별도 포트 실행 버전
"""

import streamlit as st
import sys
import os
from datetime import datetime
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

# 상위 디렉토리의 agent 모듈 import를 위한 경로 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from agent.enhanced_carbon_rag_agent import EnhancedCarbonRAGAgent
except ImportError as e:
    st.error(f"향상된 RAG 에이전트 모듈을 불러올 수 없습니다: {e}")
    st.stop()

# 페이지 설정은 main.py에서 처리됨

# iframe용 CSS - 더 컴팩트하게 수정
st.markdown("""
<style>
    .main-header {
        font-size: 24px;
        font-weight: bold;
        background: linear-gradient(90deg, #1f77b4, #ff7f0e, #2ca02c);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 20px;
    }
    .chat-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 15px;
        border-radius: 10px;
        color: white;
        margin: 10px 0;
    }
    .chat-message {
        background: rgba(255,255,255,0.1);
        padding: 8px;
        border-radius: 6px;
        margin: 6px 0;
        font-size: 12px;
    }
    .user-message {
        background: linear-gradient(135deg, #74b9ff 0%, #0984e3 100%);
        margin-left: 15%;
    }
    .assistant-message {
        background: linear-gradient(135deg, #00b894 0%, #00a085 100%);
        margin-right: 15%;
    }
    .data-info-card {
        background: white;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        margin: 10px 0;
        border-left: 3px solid #1f77b4;
        font-size: 12px;
    }
    .example-queries {
        background: linear-gradient(135deg, #fd79a8 0%, #e84393 100%);
        padding: 15px;
        border-radius: 10px;
        color: white;
        margin: 10px 0;
    }
    .stButton > button {
        width: 100%;
        margin: 3px 0;
        font-size: 11px;
        padding: 6px;
        height: auto;
    }
    .stTextInput > div > div > input {
        font-size: 12px;
        padding: 6px;
    }
    .stMarkdown {
        font-size: 12px;
    }
    .stDataFrame {
        font-size: 10px;
    }
    .stPlotlyChart {
        height: 200px;
    }
</style>
""", unsafe_allow_html=True)

# 세션 상태 초기화
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'current_query' not in st.session_state:
    st.session_state.current_query = ""
if 'auto_submit' not in st.session_state:
    st.session_state.auto_submit = False

# 타이틀
st.markdown('<h1 class="main-header">🤖 AI 챗봇</h1>', unsafe_allow_html=True)

# 에이전트 초기화
@st.cache_resource
def load_agent():
    """향상된 RAG 에이전트 로드 (캐시 사용)"""
    return EnhancedCarbonRAGAgent()

# 에이전트 로드
try:
    agent = load_agent()
except Exception as e:
    st.error(f"향상된 에이전트 초기화 실패: {e}")
    st.stop()

# 데이터 정보 표시 (축약된 버전)
with st.expander("📊 데이터 정보", expanded=False):
    data_info = agent.get_available_data_info()
    st.markdown(data_info)

# 예시 질문들 (컴팩트 버전)
st.markdown("""
<div class="example-queries">
    <h4>💡 빠른 질문</h4>
</div>
""", unsafe_allow_html=True)

example_queries = [
    "📈 총배출량 변화",
    "🏭 산업별 비교",
    "📊 연도별 추이",
    "🔍 최대 배출 분야"
]

def process_example_query(query):
    """예시 질문 처리 함수"""
    try:
        with st.spinner("분석 중..."):
            response, visualization = agent.ask(query)
            
            timestamp = datetime.now().strftime("%H:%M")
            if visualization:
                st.session_state.chat_history.append((query, response, timestamp, visualization))
            else:
                st.session_state.chat_history.append((query, response, timestamp))
    except Exception as e:
        st.error(f"오류: {e}")
    
    st.session_state.current_query = ""
    st.session_state.auto_submit = False

# 예시 질문 버튼들 (2x2 그리드)
col1, col2 = st.columns(2)
with col1:
    for i, query in enumerate(example_queries[:2]):
        if st.button(query, key=f"example_{i}"):
            process_example_query(query)

with col2:
    for i, query in enumerate(example_queries[2:], 2):
        if st.button(query, key=f"example_{i}"):
            process_example_query(query)

# 채팅 인터페이스
st.markdown("""
<div class="chat-container">
    <h4>💬 AI와 대화하기</h4>
</div>
""", unsafe_allow_html=True)

# 채팅 히스토리 표시 (최근 5개만)
recent_history = st.session_state.chat_history[-5:] if len(st.session_state.chat_history) > 5 else st.session_state.chat_history

for i, chat_item in enumerate(recent_history):
    # 채팅 항목이 튜플인지 확인 (기존 호환성)
    if len(chat_item) == 3:
        user_msg, assistant_msg, timestamp = chat_item
        visualization = None
    elif len(chat_item) == 4:
        user_msg, assistant_msg, timestamp, visualization = chat_item
    else:
        continue
    
    st.markdown(f"""
    <div class="chat-message user-message">
        <strong>사용자 ({timestamp}):</strong> {user_msg}
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"""
    <div class="chat-message assistant-message">
        <strong>AI ({timestamp}):</strong> {assistant_msg}
    </div>
    """, unsafe_allow_html=True)
    
    # 시각화가 있는 경우 표시
    if visualization:
        st.plotly_chart(visualization, use_container_width=True, height=200)

# 사용자 입력
user_input = st.text_input("질문을 입력하세요:", key="user_input", placeholder="탄소 데이터에 대해 물어보세요...")

col_input1, col_input2 = st.columns([3, 1])
with col_input1:
    if st.button("전송", key="send_button", use_container_width=True):
        if user_input:
            try:
                with st.spinner("분석 중..."):
                    response, visualization = agent.ask(user_input)
                    timestamp = datetime.now().strftime("%H:%M")
                    if visualization:
                        st.session_state.chat_history.append((user_input, response, timestamp, visualization))
                    else:
                        st.session_state.chat_history.append((user_input, response, timestamp))
                    st.rerun()
            except Exception as e:
                st.error(f"오류: {e}")

with col_input2:
    if st.button("초기화", key="clear_button", use_container_width=True):
        st.session_state.chat_history = []
        st.rerun()

# 채팅 히스토리 길이 표시
if st.session_state.chat_history:
    st.caption(f"총 {len(st.session_state.chat_history)}개의 대화 기록") 