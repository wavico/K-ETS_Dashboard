import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import json
import os
import sys

# 상위 디렉토리의 utils 모듈 import를 위한 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 페이지 설정은 main.py에서 처리됨

# 커스텀 CSS
st.markdown("""
<style>
    .info-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 25px;
        border-radius: 15px;
        color: white;
        margin: 20px 0;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    .data-source-card {
        background: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        margin: 15px 0;
        border-left: 5px solid #1f77b4;
    }
    .update-card {
        background: linear-gradient(135deg, #74b9ff 0%, #0984e3 100%);
        padding: 15px;
        border-radius: 10px;
        color: white;
        margin: 10px 0;
    }
    .system-info {
        background: linear-gradient(135deg, #00b894 0%, #00a085 100%);
        padding: 20px;
        border-radius: 15px;
        color: white;
        margin: 15px 0;
    }
    .guide-section {
        background: #f8f9fa;
        padding: 20px;
        border-radius: 10px;
        margin: 15px 0;
        border: 1px solid #e9ecef;
    }
</style>
""", unsafe_allow_html=True)

# 타이틀
st.markdown('<h1 style="text-align:center; color:#1f77b4;">📋 프로그램 정보</h1>', unsafe_allow_html=True)

# 사이드바 - 정보 필터링
with st.sidebar:
    st.header("🔍 정보 필터")
    
    # 카테고리 선택
    selected_category = st.multiselect(
        "카테고리 선택",
        ["데이터 소스", "업데이트 히스토리", "시스템 정보", "사용 가이드", "기술 스택"],
        default=["데이터 소스", "업데이트 히스토리"]
    )
    
    # 날짜 필터
    st.subheader("📅 날짜 범위")
    start_date = st.date_input("시작일", datetime(2024, 1, 1))
    end_date = st.date_input("종료일", datetime.now())
    
    # 검색
    search_term = st.text_input("🔍 검색어", placeholder="키워드를 입력하세요...")

# 1. 📁 데이터 소스 정보
if "데이터 소스" in selected_category:
    st.markdown('<div class="info-container">', unsafe_allow_html=True)
    st.subheader("📁 데이터 소스")
    
    data_sources = {
        "국가 온실가스 인벤토리": {
            "제공기관": "환경부",
            "기간": "1990-2021",
            "데이터형태": "CSV",
            "업데이트주기": "연 1회",
            "설명": "국가별 온실가스 배출량 통계 데이터",
            "파일명": "환경부 온실가스종합정보센터_국가 온실가스 인벤토리 배출량_20250103.csv"
        },
        "배출권 거래데이터": {
            "제공기관": "한국환경공단",
            "기간": "2021-현재",
            "데이터형태": "CSV",
            "업데이트주기": "일 1회",
            "설명": "KAU24 등 배출권 거래 시장 데이터",
            "파일명": "배출권_거래데이터.csv"
        },
        "3차 사전할당": {
            "제공기관": "환경부",
            "기간": "2021-2025",
            "데이터형태": "CSV",
            "업데이트주기": "연 1회",
            "설명": "3차 사전할당 대상 업체별 할당량",
            "파일명": "01. 3차_사전할당_20250613090824.csv"
        },
        "지역별 CO₂ 농도": {
            "제공기관": "기상청/환경부",
            "기간": "2020-현재",
            "데이터형태": "Excel",
            "업데이트주기": "월 1회",
            "설명": "지역별 이산화탄소 농도 측정 데이터",
            "파일명": "기업_규모_지역별_온실가스_배출량_20250615183643.xlsx"
        },
        "기업 배출량": {
            "제공기관": "한국에너지공단",
            "기간": "2020-현재",
            "데이터형태": "CSV",
            "업데이트주기": "분기 1회",
            "설명": "산업부문 에너지사용 및 온실가스배출량 통계",
            "파일명": "한국에너지공단_산업부문 에너지사용 및 온실가스배출량 통계_20231231.csv"
        }
    }
    
    for source_name, source_info in data_sources.items():
        if not search_term or search_term.lower() in source_name.lower() or search_term.lower() in source_info["설명"].lower():
            with st.container():
                st.markdown(f"""
                ### {source_name}
                - **제공기관**: {source_info['제공기관']}
                - **기간**: {source_info['기간']}
                - **데이터형태**: {source_info['데이터형태']}
                - **업데이트주기**: {source_info['업데이트주기']}
                - **설명**: {source_info['설명']}
                - **파일명**: `{source_info['파일명']}`
                """)
                st.markdown("---")
    
    st.markdown('</div>', unsafe_allow_html=True)

# 2. 🔄 업데이트 히스토리
if "업데이트 히스토리" in selected_category:
    st.markdown('<div class="info-container">', unsafe_allow_html=True)
    st.subheader("🔄 업데이트 히스토리")
    
    updates = [
        {
            "날짜": "2024-01-15",
            "버전": "v2.0.0",
            "제목": "ESG 랭킹 시스템 메인 페이지 통합 완료",
            "설명": "ESG 기반 탄소 감축 랭킹 시스템을 메인 페이지에 완전 통합",
            "카테고리": "기능 추가",
            "상세내용": [
                "🥇 ESG 랭킹 보드 구현",
                "🥈 KPI 비교 시스템 추가",
                "🥉 Gamification 배지 시스템",
                "🧠 AI 시뮬레이터 통합"
            ]
        },
        {
            "날짜": "2024-01-14",
            "버전": "v1.3.0",
            "제목": "AI 챗봇 시나리오 시뮬레이션 추가",
            "설명": "대화형 AI 챗봇을 통한 What-if 분석 기능 구현",
            "카테고리": "기능 추가",
            "상세내용": [
                "💬 자연어 입력 처리",
                "📊 시나리오 시뮬레이션",
                "🎯 전략 추천 시스템",
                "📈 결과 시각화"
            ]
        },
        {
            "날짜": "2024-01-13",
            "버전": "v1.2.0",
            "제목": "구매 전략 대시보드 개발",
            "설명": "탄소배출권 구매 전략을 위한 전문 대시보드 구현",
            "카테고리": "기능 추가",
            "상세내용": [
                "🔔 알림 시스템",
                "📈 타이밍 분석",
                "♻️ 대체 전략 분석",
                "💹 헤징 전략",
                "📄 AI 리포트"
            ]
        },
        {
            "날짜": "2024-01-12",
            "버전": "v1.1.0",
            "제목": "실시간 데이터 연동 완료",
            "설명": "실제 CSV 데이터 파일과 연동하여 정확한 분석 제공",
            "카테고리": "데이터 연동",
            "상세내용": [
                "📁 CSV 파일 로드",
                "🔧 인코딩 문제 해결",
                "📊 데이터 전처리",
                "🎯 정확한 시각화"
            ]
        },
        {
            "날짜": "2024-01-11",
            "버전": "v1.0.0",
            "제목": "초기 버전 출시",
            "설명": "탄소배출권 통합 관리 시스템 첫 출시",
            "카테고리": "초기 출시",
            "상세내용": [
                "🌍 기본 대시보드",
                "📊 차트 시각화",
                "🔍 필터링 기능",
                "📱 반응형 디자인"
            ]
        }
    ]
    
    for update in updates:
        update_date = datetime.strptime(update["날짜"], "%Y-%m-%d").date()
        if start_date <= update_date <= end_date:
            if not search_term or search_term.lower() in update["제목"].lower() or search_term.lower() in update["설명"].lower():
                st.markdown('<div class="update-card">', unsafe_allow_html=True)
                st.markdown(f"""
                ### {update['날짜']} - {update['제목']} (v{update['버전']})
                **{update['설명']}**
                
                **카테고리**: {update['카테고리']}
                
                **상세 내용**:
                """)
                for detail in update['상세내용']:
                    st.markdown(f"- {detail}")
                st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

# 3. 💻 시스템 정보
if "시스템 정보" in selected_category:
    st.markdown('<div class="system-info">', unsafe_allow_html=True)
    st.subheader("💻 시스템 정보")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### 🏗️ 아키텍처
        - **프레임워크**: Streamlit
        - **언어**: Python 3.9+
        - **데이터베이스**: 파일 기반 (CSV/Excel)
        - **배포**: 로컬/클라우드
        
        ### 📊 데이터 처리
        - **시각화**: Plotly
        - **데이터 분석**: Pandas, NumPy
        - **차트**: Plotly Express, Graph Objects
        - **이미지 처리**: PIL (Pillow)
        """)
    
    with col2:
        st.markdown("""
        ### 🔧 기술 스택
        - **프론트엔드**: Streamlit Components
        - **백엔드**: Python
        - **데이터**: CSV, Excel, JSON
        - **스타일링**: CSS3, HTML5
        
        ### 📁 파일 구조
        ```
        Dash_carbon_dashboard/
        ├── main.py
        ├── pages/
        │   ├── 1_현황_대시보드.py
        │   ├── 2_구매_전략.py
        │   └── 4_프로그램_정보.py
        └── data/
            └── *.csv, *.xlsx
        ```
        """)
    
    st.markdown('</div>', unsafe_allow_html=True)

# 4. 📖 사용 가이드
if "사용 가이드" in selected_category:
    st.markdown('<div class="guide-section">', unsafe_allow_html=True)
    st.subheader("📖 사용 가이드")
    
    st.markdown("""
    ### 🎯 **1단계: 현황 파악**
    1. **메인 페이지**에서 전체 시스템 개요 확인
    2. **사이드바 설정**에서 기업 정보 입력
    3. **ESG 랭킹 시스템**에서 현재 순위 확인
    
    ### 💡 **2단계: 전략 수립**
    1. **현황 대시보드**에서 시장 상황 분석
    2. **구매 전략 대시보드**에서 투자 방향 결정
    3. **AI 시뮬레이터**에서 개선 전략 수립
    
    ### 📈 **3단계: 실행 및 모니터링**
    1. 수립된 전략 실행
    2. **트렌드 추적**으로 성과 모니터링
    3. **배지 시스템**으로 성과 공유
    """)
    
    st.markdown("""
    ### 🔧 **기술적 가이드**
    
    #### 데이터 업로드
    - CSV 파일은 UTF-8 또는 CP949 인코딩 지원
    - Excel 파일은 .xlsx 형식 권장
    - 파일 크기는 100MB 이하 권장
    
    #### 성능 최적화
    - 대용량 데이터는 샘플링 후 처리
    - 차트는 Plotly로 인터랙티브 구현
    - 캐싱을 통한 로딩 속도 개선
    """)
    
    st.markdown('</div>', unsafe_allow_html=True)

# 5. 🛠️ 기술 스택
if "기술 스택" in selected_category:
    st.markdown('<div class="guide-section">', unsafe_allow_html=True)
    st.subheader("🛠️ 기술 스택")
    
    tech_stack = {
        "프론트엔드": {
            "Streamlit": "웹 애플리케이션 프레임워크",
            "HTML/CSS": "스타일링 및 레이아웃",
            "JavaScript": "인터랙티브 기능"
        },
        "백엔드": {
            "Python": "주요 프로그래밍 언어",
            "Pandas": "데이터 처리 및 분석",
            "NumPy": "수치 계산",
            "PIL": "이미지 처리"
        },
        "데이터 시각화": {
            "Plotly": "인터랙티브 차트",
            "Plotly Express": "간단한 시각화",
            "Graph Objects": "고급 차트"
        },
        "데이터 저장": {
            "CSV": "주요 데이터 형식",
            "Excel": "스프레드시트 데이터",
            "JSON": "설정 및 메타데이터"
        },
        "배포": {
            "Streamlit Cloud": "클라우드 배포",
            "Docker": "컨테이너화",
            "Git": "버전 관리"
        }
    }
    
    for category, technologies in tech_stack.items():
        st.markdown(f"### {category}")
        for tech, description in technologies.items():
            st.markdown(f"- **{tech}**: {description}")
        st.markdown("")
    
    st.markdown('</div>', unsafe_allow_html=True)

# 정보 내보내기 기능
st.markdown("---")
st.subheader("📤 정보 내보내기")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("📄 PDF 리포트 생성"):
        st.success("PDF 리포트 생성 중... (실제 구현 시 PDF 생성 로직 추가)")

with col2:
    if st.button("📊 Excel 데이터 내보내기"):
        # 데이터를 Excel로 내보내기
        df_sources = pd.DataFrame([
            {"데이터소스": k, "제공기관": v["제공기관"], "기간": v["기간"]}
            for k, v in data_sources.items()
        ])
        
        df_updates = pd.DataFrame([
            {"날짜": u["날짜"], "제목": u["제목"], "설명": u["설명"]}
            for u in updates
        ])
        
        # Excel 파일 생성
        with pd.ExcelWriter("프로그램_정보.xlsx") as writer:
            df_sources.to_excel(writer, sheet_name="데이터소스", index=False)
            df_updates.to_excel(writer, sheet_name="업데이트", index=False)
        
        st.success("Excel 파일이 생성되었습니다!")

with col3:
    if st.button("🔄 정보 새로고침"):
        st.rerun()

# 플로팅 챗봇 버튼 제거됨

# 푸터
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #888; margin-top: 50px;'>
        <p>📋 프로그램 정보 | 탄소배출권 통합 관리 시스템</p>
        <p>최신 업데이트: 2024-01-15 | 버전: v2.0.0</p>
    </div>
    """, 
    unsafe_allow_html=True
) 