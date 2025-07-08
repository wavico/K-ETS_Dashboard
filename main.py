import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime, timedelta
import json 
import os
import base64
from PIL import Image, ImageDraw, ImageFont
import io
from dotenv import load_dotenv
import sys
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Literal
import asyncio
from fastapi.responses import StreamingResponse, Response
from utils import create_docx, create_pdf
from urllib.parse import quote

# .env 파일 로드
try:
    load_dotenv()
    # .env 파일이 없거나 로드에 실패한 경우 경고 메시지 출력
    if not os.getenv('UPSTAGE_API_KEY'):
        print("⚠️ UPSTAGE_API_KEY가 설정되지 않았습니다. env.example 파일을 참고하여 .env 파일을 생성해주세요.")
except Exception as e:
    print(f"환경변수 로드 중 오류 (무시됨): {e}")
    print("⚠️ .env 파일을 확인해주세요. env.example 파일을 참고하여 .env 파일을 생성할 수 있습니다.")

# 페이지 설정
st.set_page_config(
    page_title="탄소배출권 통합 관리 시스템",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 사이드바 제어를 위한 JavaScript 추가
st.markdown("""
<script>
window.addEventListener('message', function(event) {
    if (event.origin !== 'http://localhost:3000') return;
    
    if (event.data.type === 'TOGGLE_SIDEBAR') {
        const sidebar = document.querySelector('[data-testid="stSidebar"]');
        if (sidebar) {
            if (event.data.sidebarState === 'collapsed') {
                sidebar.style.transform = 'translateX(-100%)';
                sidebar.style.transition = 'transform 0.3s ease';
            } else {
                sidebar.style.transform = 'translateX(0)';
                sidebar.style.transition = 'transform 0.3s ease';
            }
        }
    }
});
</script>
""", unsafe_allow_html=True)

# 커스텀 CSS
st.markdown("""
<style>
    .main-header {
        font-size: 36px;
        font-weight: bold;
        background: linear-gradient(90deg, #1f77b4, #ff7f0e, #2ca02c);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 40px;
    }
    .welcome-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 30px;
        border-radius: 20px;
        color: white;
        margin: 20px 0;
        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
    }
    .feature-card {
        background: white;
        padding: 25px;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        margin: 15px 0;
        border-left: 5px solid #1f77b4;
        transition: transform 0.3s ease;
    }
    .feature-card:hover {
        transform: translateY(-5px);
    }
    .metric-highlight {
        background: linear-gradient(135deg, #74b9ff 0%, #0984e3 100%);
        padding: 20px;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin: 15px 0;
    }
    .quick-stats {
        display: flex;
        justify-content: space-around;
        margin: 20px 0;
    }
    .stat-item {
        text-align: center;
        padding: 15px;
        background: rgba(255,255,255,0.1);
        border-radius: 10px;
        margin: 0 10px;
    }
    .ranking-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 15px;
        color: white;
        margin: 15px 0;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    .badge-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 30px;
        border-radius: 20px;
        color: white;
        margin: 20px 0;
        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
        text-align: left;
    }
    .simulator-container {
        background: linear-gradient(135deg, #00b894 0%, #00a085 100%);
        padding: 20px;
        border-radius: 15px;
        color: white;
        margin: 15px 0;
    }
</style>
""", unsafe_allow_html=True)

# 타이틀
st.markdown('<h1 class="main-header">🌍 탄소배출권 통합 관리 시스템</h1>', unsafe_allow_html=True)

# 환영 메시지
st.markdown("""
<div class="welcome-container">
    <h2>🎯 통합 탄소배출권 관리 플랫폼</h2>
    <p><strong>탄소배출량 모니터링부터 구매 전략 수립까지, 모든 것을 한 곳에서 관리하세요.</strong></p>
    <p>이 시스템은 기업의 탄소배출권 관리를 위한 종합 솔루션을 제공합니다.<br>
    실시간 데이터 기반 분석과 AI 기반 전략 추천으로 최적의 의사결정을 지원합니다.</p>
</div>
""", unsafe_allow_html=True)

# 주요 통계 (샘플 데이터)
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown("""
    <div class="metric-highlight">
        <div data-testid="metric-container">
            <div data-testid="metric">
                <div data-testid="metric-label">📊 총 배출량</div>
                <div data-testid="metric-value">676,648 Gg CO₂eq</div>
                <div data-testid="metric-delta">2021년 기준</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="metric-highlight">
        <div data-testid="metric-container">
            <div data-testid="metric">
                <div data-testid="metric-label">💹 KAU24 가격</div>
                <div data-testid="metric-value">8,770원</div>
                <div data-testid="metric-delta">+2.3%</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="metric-highlight">
        <div data-testid="metric-container">
            <div data-testid="metric">
                <div data-testid="metric-label">🏭 할당 대상</div>
                <div data-testid="metric-value">1,247개 업체</div>
                <div data-testid="metric-delta">3차 사전할당</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown("""
    <div class="metric-highlight">
        <div data-testid="metric-container">
            <div data-testid="metric">
                <div data-testid="metric-label">🎯 감축 목표</div>
                <div data-testid="metric-value">40%</div>
                <div data-testid="metric-delta">2030년까지</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# 주요 기능 소개
st.markdown("## 🚀 주요 기능")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    <div style="background: white; padding: 25px; border-radius: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); margin: 15px 0; border-left: 5px solid #1f77b4;">
        <h3>📊 현황 대시보드</h3>
        <ul>
            <li><strong>실시간 모니터링</strong>: 연도별 배출량, 지역별 CO₂ 농도</li>
            <li><strong>시장 분석</strong>: KAU24 가격/거래량 추이</li>
            <li><strong>할당량 현황</strong>: 업종별/업체별 분포</li>
            <li><strong>AI 챗봇</strong>: 시나리오 시뮬레이션</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div style="background: white; padding: 25px; border-radius: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); margin: 15px 0; border-left: 5px solid #1f77b4;">
        <h3>🎯 구매 전략 대시보드</h3>
        <ul>
            <li><strong>알림 시스템</strong>: 정책/가격 급등 예고</li>
            <li><strong>타이밍 분석</strong>: 최적 매수 시점 추천</li>
            <li><strong>ROI 비교</strong>: 감축 vs 구매 전략 분석</li>
            <li><strong>헤징 전략</strong>: ETF/선물 연계 포트폴리오</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

# ESG 기반 탄소 감축 랭킹 시스템 구현
st.markdown('---')
st.markdown('<h2 style="text-align:center;">🏆 ESG 기반 탄소 감축 랭킹 시스템</h2>', unsafe_allow_html=True)

# 사이드바 설정
with st.sidebar:
    st.header("⚙️ ESG 설정")
    
    # 기업 정보
    st.subheader("🏢 기업 정보")
    company_name = st.text_input("기업명", "삼성전자")
    industry = st.selectbox("업종", ["전자제품", "철강", "화학", "자동차", "건설", "에너지"])
    
    # 현재 ESG 점수
    current_esg_score = st.slider("현재 ESG 점수", 0, 100, 75)
    current_reduction_rate = st.slider("현재 감축률 (%)", 0, 50, 15)
    current_allocation_ratio = st.slider("할당 대비 보유율 (%)", 50, 200, 120)
    
    # 목표 설정
    st.subheader("🎯 목표 설정")
    target_esg_score = st.slider("목표 ESG 점수", 0, 100, 85)
    target_reduction_rate = st.slider("목표 감축률 (%)", 0, 50, 25)

# 1. 🥇 탄소 감축 성과 기반 ESG 랭킹 보드
st.markdown("""
<div class="ranking-card">
    <h3>🥇 탄소 감축 성과 기반 ESG 랭킹 보드</h3>
</div>
""", unsafe_allow_html=True)

# 샘플 랭킹 데이터 생성
industries = ["전자제품", "철강", "화학", "자동차", "건설", "에너지"]
companies = ["삼성전자", "포스코", "LG화학", "현대자동차", "현대건설", "한국전력"]
ranking_data = []

for i, (ind, comp) in enumerate(zip(industries, companies)):
    # 랭킹 점수 계산 (감축률, 할당 효율성, ESG 점수 종합)
    reduction_rate = np.random.uniform(10, 30)
    allocation_efficiency = np.random.uniform(80, 150)
    esg_score = np.random.uniform(60, 95)
    
    # 종합 점수 계산
    total_score = (reduction_rate * 0.4 + 
                  (allocation_efficiency/100) * 30 + 
                  esg_score * 0.3)
    
    ranking_data.append({
        '순위': i + 1,
        '기업명': comp,
        '업종': ind,
        '감축률(%)': round(reduction_rate, 1),
        '할당효율성(%)': round(allocation_efficiency, 1),
        'ESG점수': round(esg_score, 1),
        '종합점수': round(total_score, 1)
    })

ranking_df = pd.DataFrame(ranking_data)

# 랭킹 테이블
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📊 업종별 ESG 랭킹")
    st.dataframe(ranking_df, use_container_width=True)

with col2:
    st.subheader("🏆 현재 기업 순위")
    current_rank = ranking_df[ranking_df['기업명'] == company_name]['순위'].iloc[0] if company_name in ranking_df['기업명'].values else "N/A"
    st.metric("현재 순위", f"{current_rank}위", "상위 20%")
    
    # ESG 등급
    if current_esg_score >= 90:
        grade = "A+"
        color = "🟢"
    elif current_esg_score >= 80:
        grade = "A"
        color = "🟢"
    elif current_esg_score >= 70:
        grade = "B+"
        color = "🟡"
    elif current_esg_score >= 60:
        grade = "B"
        color = "🟡"
    else:
        grade = "C"
        color = "🔴"
    
    st.metric("ESG 등급", f"{color} {grade}", f"{current_esg_score}점")

# 트렌드 추적 그래프
st.subheader("📈 ESG 등급 추세")
trend_data = []
for month in range(1, 13):
    trend_data.append({
        '월': f"2024-{month:02d}",
        'ESG점수': current_esg_score + np.random.normal(0, 2),
        '감축률': current_reduction_rate + np.random.normal(0, 1)
    })

trend_df = pd.DataFrame(trend_data)

fig_trend = make_subplots(specs=[[{"secondary_y": True}]])
fig_trend.add_trace(
    go.Scatter(x=trend_df['월'], y=trend_df['ESG점수'], name="ESG 점수", line=dict(color='blue')),
    secondary_y=False
)
fig_trend.add_trace(
    go.Scatter(x=trend_df['월'], y=trend_df['감축률'], name="감축률 (%)", line=dict(color='red')),
    secondary_y=True
)
fig_trend.update_layout(title="월별 ESG 점수 및 감축률 추이", height=400)
st.plotly_chart(fig_trend, use_container_width=True)

# 2. 🥈 업종별·기업별 탄소 KPI 비교 페이지
st.markdown("""
<div class="ranking-card">
    <h3>🥈 업종별·기업별 탄소 KPI 비교</h3>
</div>
""", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div class="metric-highlight">
        <div data-testid="metric-container">
            <div data-testid="metric">
                <div data-testid="metric-label">총배출량 대비 감축률</div>
                <div data-testid="metric-value">"""+f"{current_reduction_rate}%"+"""</div>
                <div data-testid="metric-delta">업종 평균 """+f"{ranking_df[ranking_df['업종'] == industry]['감축률(%)'].mean():.1f}%"+"""</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="metric-highlight">
        <div data-testid="metric-container">
            <div data-testid="metric">
                <div data-testid="metric-label">할당 대비 잉여율</div>
                <div data-testid="metric-value">"""+f"{current_allocation_ratio}%"+"""</div>
                <div data-testid="metric-delta">"""+"탄소 여유 있음" if current_allocation_ratio > 100 else "부족"+"""</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    trading_efficiency = np.random.uniform(60, 95)
    st.markdown("""
    <div class="metric-highlight">
        <div data-testid="metric-container">
            <div data-testid="metric">
                <div data-testid="metric-label">거래 활용도</div>
                <div data-testid="metric-value">"""+f"{trading_efficiency:.1f}%"+"""</div>
                <div data-testid="metric-delta">"""+"효율적" if trading_efficiency > 80 else "개선 필요"+"""</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# KPI 비교 차트
fig_kpi = px.scatter(ranking_df, x='감축률(%)', y='ESG점수', 
                     size='종합점수', color='업종',
                     hover_name='기업명', title="감축률 vs ESG 점수 비교")
st.plotly_chart(fig_kpi, use_container_width=True)

# 3. 🥉 Gamification: ESG 등급 배지 + 소셜 공유
st.markdown("""
<div class="badge-container">
    <h3>🥉 ESG 등급 배지 + 소셜 공유</h3>
</div>
""", unsafe_allow_html=True)

# 배지 생성 함수
def create_esg_badge(grade, company_name, score):
    # 배지 이미지 생성
    img = Image.new('RGB', (400, 200), color='white')
    draw = ImageDraw.Draw(img)
    
    # 배지 디자인
    if grade == "A+":
        color = (255, 215, 0)  # Gold
        medal = "🥇"
    elif grade == "A":
        color = (192, 192, 192)  # Silver
        medal = "🥈"
    else:
        color = (205, 127, 50)  # Bronze
        medal = "🥉"
    
    # 배지 그리기
    draw.ellipse([50, 50, 350, 150], outline=color, width=5)
    
    # 텍스트 추가
    try:
        font = ImageFont.truetype("arial.ttf", 20)
    except:
        font = ImageFont.load_default()
    
    draw.text((200, 80), medal, fill=color, anchor="mm", font=font)
    draw.text((200, 110), f"{grade} 등급", fill=color, anchor="mm", font=font)
    draw.text((200, 140), f"{company_name}", fill=(0, 0, 0), anchor="mm", font=font)
    draw.text((200, 160), f"ESG 점수: {score}", fill=(0, 0, 0), anchor="mm", font=font)
    
    return img

# 배지 생성 및 표시
badge_img = create_esg_badge(grade, company_name, current_esg_score)

col1, col2 = st.columns([1, 1])

with col1:
    st.image(badge_img, caption=f"{company_name} ESG 배지", use_column_width=True)

with col2:
    st.markdown("""
    <div style="padding: 20px;">
        <h4>🏆 ESG 성과 공유</h4>
        <p>당신의 ESG 성과를 소셜 미디어에 공유하세요!</p>
        <ul>
            <li>📱 LinkedIn에 공유</li>
            <li>🐦 Twitter에 공유</li>
            <li>📧 이메일로 전송</li>
            <li>💾 이미지 다운로드</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    # 공유 버튼들
    col_share1, col_share2 = st.columns(2)
    with col_share1:
        if st.button("📱 LinkedIn 공유"):
            st.success("LinkedIn 공유 링크가 생성되었습니다!")
    with col_share2:
        if st.button("🐦 Twitter 공유"):
            st.success("Twitter 공유 링크가 생성되었습니다!")

# 자동 새로고침 (선택사항)
# st_autorefresh(interval=30000, key="data_refresh")  # 30초마다 새로고침 

### FastAPI 시작 ###
# --- 프로젝트 루트를 sys.path에 추가 ---
# 이 스크립트가 다른 모듈(예: agent)을 올바르게 임포트할 수 있도록 프로젝트의 루트 디렉토리를 시스템 경로에 추가합니다.
try:
    project_root = os.path.dirname(os.path.abspath(__file__))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    # 에이전트 클래스 임포트
    from agent.agent_template import ReportTemplateAgent
    from agent.enhanced_carbon_rag_agent import EnhancedCarbonRAGAgent
except Exception as e:
    print(f"경로 추가 또는 에이전트 임포트 중 오류 발생: {e}")
    sys.exit(1)


# --- 에이전트 초기화 ---
# FastAPI 앱 시작 시 에이전트를 한 번만 로드하여 효율성을 높입니다.
try:
    template_agent = ReportTemplateAgent()
    report_agent = EnhancedCarbonRAGAgent()
    print("✅ 모든 에이전트가 성공적으로 초기화되었습니다.")
except Exception as e:
    print(f"❌ 에이전트 초기화 실패: {e}")
    template_agent = None
    report_agent = None


# --- FastAPI 앱 초기화 ---
app = FastAPI(
    title="K-ETS 대시보드 AI 보고서 생성기 API",
    description="주제를 기반으로 보고서의 목차를 생성하고, 목차에 따라 본문을 스트리밍하는 API입니다.",
    version="1.0.0"
)

# --- CORS 미들웨어 설정 ---
# 모든 출처에서의 요청을 허용합니다 (개발 환경용).
# 프로덕션 환경에서는 특정 출처만 허용하도록 수정해야 합니다.
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # 모든 HTTP 메소드 허용
    allow_headers=["*"],  # 모든 HTTP 헤더 허용
)


# --- Pydantic 데이터 모델 정의 ---

# /generate-outline-from-topic 엔드포인트 요청 본문
class TopicRequest(BaseModel):
    topic: str = Field(..., 
                       description="생성할 보고서의 주제",
                       example="국내 탄소 배출 현황 및 감축 전략")

# /generate-outline-from-topic 엔드포인트 응답 본문
class OutlineResponse(BaseModel):
    template_text: str = Field(..., 
                               description="LLM이 생성한 보고서의 뼈대(템플릿) 텍스트")
    outline: Dict[str, Any] = Field(..., 
                                    description="템플릿 텍스트를 기반으로 생성된 구조화된 목차(JSON)")


# /generate-report 엔드포인트 요청 본문
class ReportRequest(BaseModel):
    topic: str = Field(..., description="원본 보고서 주제")
    outline: Dict[str, Any] = Field(..., description="사용자가 수정 완료한 최종 목차 JSON")

class ReportDownloadRequest(BaseModel):
    title: str = Field(..., description="보고서 제목")
    content: str = Field(..., description="생성된 보고서의 전체 텍스트 내용")


# --- API 엔드포인트 구현 ---

@app.get("/", summary="API 상태 확인")
async def read_root():
    """API 서버가 정상적으로 실행 중인지 확인하는 기본 엔드포인트입니다."""
    return {"status": "K-ETS AI Report Generator API is running"}

@app.post("/generate-outline-from-topic", response_model=OutlineResponse, summary="주제 기반 보고서 구조 생성")
async def generate_outline(request: TopicRequest):
    """
    사용자가 입력한 주제를 받아, 보고서 템플릿(텍스트)과 구조화된 목차(JSON)를 생성하여 반환합니다.
    """
    if not template_agent:
        raise HTTPException(status_code=503, detail="보고서 구조 생성 에이전트를 사용할 수 없습니다.")

    topic = request.topic
    print(f"--- 주제 기반 구조 생성 요청: '{topic}' ---")

    try:
        template_text = template_agent.generate_report_template(topic)
        if not template_text:
            raise HTTPException(status_code=500, detail="보고서 템플릿 생성에 실패했습니다.")

        outline_json = template_agent.generate_structured_outline(template_text)
        if not outline_json:
            raise HTTPException(status_code=500, detail="구조화된 목차 생성에 실패했습니다.")

        print("--- ✅ 구조 생성 완료 ---")
        return OutlineResponse(template_text=template_text, outline=outline_json)
    except Exception as e:
        print(f"❌ 구조 생성 중 오류 발생: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def report_streamer(topic: str, outline: Dict[str, Any]):
    """목차(outline)를 순회하며 각 섹션의 내용을 생성하고 스트리밍하는 비동기 제너레이터"""

    async def _traverse_outline(outline_nodes: List[Dict[str, Any]]):
        """재귀적으로 목차 노드를 탐색하고 컨텐츠를 생성"""
        for node in outline_nodes:
            section_title = node.get("title", "제목 없음")
            
            # 섹션 제목 스트리밍
            title_payload = {"type": "section_title", "payload": section_title}
            yield f"data: {json.dumps(title_payload, ensure_ascii=False)}\n\n"
            await asyncio.sleep(0.1)

            # 에이전트에게 전달할 구체적인 질문 생성
            question = f"'{topic}'에 대한 보고서를 작성 중입니다. '{section_title}' 섹션에 들어갈 내용을 데이터와 문서를 기반으로 분석하고, 전문적인 보고서 형식의 서술형 문장으로 작성해주세요."
            
            content_stream = None
            try:
                # run_in_executor를 사용하여 동기 함수를 비동기적으로 실행
                loop = asyncio.get_running_loop()
                agent_response = await loop.run_in_executor(
                    None,  # 기본 스레드 풀 실행기 사용
                    report_agent.ask,
                    question,
                    section_title
                )
                # [수정] Agent 응답이 튜플이므로, 첫 번째 요소(본문)를 content_stream으로 사용
                content_stream = agent_response[0] if isinstance(agent_response, tuple) and agent_response else None

            except Exception as e:
                # [DEBUG] 에이전트 호출 중 에러 발생 시 로그 출력
                print("-" * 50)
                print(f"!!! Agent 호출 중 에러 발생 ('{section_title}') !!!")
                print(f"에러: {e}")
                print("-" * 50)
                error_payload = {"type": "error", "payload": f"'{section_title}' 생성 중 에러: {e}"}
                yield f"data: {json.dumps(error_payload, ensure_ascii=False)}\n\n"

            # [DEBUG] Agent가 반환한 실제 내용을 서버 터미널에 출력
            print("-" * 50)
            print(f"Agent 응답 ('{section_title}'):")
            print(f"응답 내용: {content_stream}")
            print(f"타입: {type(content_stream)}")
            print("-" * 50)

            if content_stream and isinstance(content_stream, str):
                # 생성된 내용을 문단별로 나누어 스트리밍
                paragraphs = content_stream.split('\n')
                for para in paragraphs:
                    if para.strip():
                        content_payload = {"type": "content", "payload": para.strip()}
                        yield f"data: {json.dumps(content_payload, ensure_ascii=False)}\n\n"
                        await asyncio.sleep(0.05)

            # 하위 섹션이 있으면 재귀적으로 처리
            if "sections" in node and node["sections"]:
                async for item in _traverse_outline(node["sections"]):
                    yield item

    # 최상위 챕터부터 순회 시작
    if "chapters" in outline and outline["chapters"]:
        async for item in _traverse_outline(outline["chapters"]):
            yield item
    
    # 모든 작업 완료 신호 전송
    done_payload = {"type": "done", "payload": "보고서 생성이 완료되었습니다."}
    yield f"data: {json.dumps(done_payload, ensure_ascii=False)}\n\n"


@app.post("/generate-report", summary="보고서 본문 생성 및 실시간 스트리밍")
async def generate_report_streaming(request: ReportRequest):
    """
    사용자가 수정한 최종 목차를 받아, 각 섹션의 본문을 실시간으로 생성하여 Server-Sent Events (SSE)로 스트리밍
    """
    topic = request.topic
    outline = request.outline
    return StreamingResponse(report_streamer(topic, outline), media_type="text/event-stream")

@app.post("/download-report", summary="생성된 보고서를 파일로 다운로드")
async def download_report(
    request: ReportDownloadRequest,
    format: Literal['docx', 'pdf'] = 'docx'
):
    """
    클라이언트로부터 받은 보고서의 전체 텍스트를
    지정된 파일 형식(DOCX 또는 PDF)으로 변환하여 다운로드합니다.

    - **request**: 보고서의 제목과 전체 내용이 포함된 JSON.
    - **format**: 'docx' 또는 'pdf'. 기본값은 'docx'.
    """
    title = request.title
    content = request.content
    
    if format == 'docx':
        file_stream = create_docx(title, content)
        media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        filename = f"{title}.docx"
    elif format == 'pdf':
        file_stream = create_pdf(title, content)
        media_type = "application/pdf"
        filename = f"{title}.pdf"
    else:
        # 이 경우는 Literal 타입으로 인해 발생하지 않지만, 안정성을 위해 추가
        return Response(status_code=400, content="Unsupported file format")

    # 한글 파일명이 깨지지 않도록 URL 인코딩
    encoded_filename = quote(filename)
    headers = {
        'Content-Disposition': f"attachment; filename*=UTF-8''{encoded_filename}"
    }
    
    return Response(content=file_stream.read(), media_type=media_type, headers=headers)


# --- 서버 실행 (Uvicorn) ---
if __name__ == "__main__":
    import uvicorn
    # Use environment variable to control reload
    is_dev = os.getenv("ENVIRONMENT", "development") == "development"
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=is_dev)