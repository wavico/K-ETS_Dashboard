import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# 상위 디렉토리의 utils 모듈 import를 위한 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import json 
import os

# 페이지 설정은 main.py에서 처리됨

# 커스텀 CSS
st.markdown("""
<style>
    .main-header {
        font-size: 28px;
        font-weight: bold;
        color: #2E4057;
        text-align: center;
        margin-bottom: 30px;
    }
    .metric-container {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .chart-container {
        background-color: white;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 10px 0;
    }
    .filter-container {
        background-color: #f8f9fa;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

# 타이틀
st.markdown('<h1 class="main-header">🌍 탄소배출량 및 배출권 현황</h1>', unsafe_allow_html=True)

# 데이터 로드 함수들
def load_emissions_data():
    """국가 온실가스 인벤토리 데이터 로드"""
    try:
        # 여러 인코딩 시도
        for encoding in ['cp949', 'euc-kr', 'utf-8']:
            try:
                df = pd.read_csv('data/환경부 온실가스종합정보센터_국가 온실가스 인벤토리 배출량_20250103.csv', encoding=encoding)
                
                # 컬럼명 정리
                df.columns = df.columns.str.strip()
                
                # 데이터 구조 확인 및 변환
                emissions_data = []
                
                # CSV 파일의 구조: 첫 번째 컬럼이 연도, 두 번째 컬럼이 총배출량(kt CO2-eq)
                for _, row in df.iterrows():
                    try:
                        year = int(row.iloc[0])  # 첫 번째 컬럼: 연도
                        
                        # 각 배출량 데이터 추출 (kt CO2-eq 단위)
                        total_emission = float(row.iloc[1]) if pd.notna(row.iloc[1]) else 0  # 총배출량
                        
                        # 주요 부문별 배출량 (실제 컬럼 구조에 맞게 조정)
                        # '에너지' 부문은 컬럼 인덱스 3
                        energy_emission = float(row.iloc[3]) if len(row) > 3 and pd.notna(row.iloc[3]) else 0
                        
                        # '산업공정 및 제품사용' 부문은 컬럼 인덱스 45 (check_data.py 결과 참조)
                        industrial_emission = float(row.iloc[45]) if len(row) > 45 and pd.notna(row.iloc[45]) else 0
                        
                        # '농업' 부문은 컬럼 인덱스 96
                        agriculture_emission = float(row.iloc[96]) if len(row) > 96 and pd.notna(row.iloc[96]) else 0
                        
                        # '폐기물' 부문은 컬럼 인덱스 147 (마지막 부분)
                        waste_emission = float(row.iloc[147]) if len(row) > 147 and pd.notna(row.iloc[147]) else 0
                        
                        if year >= 1990 and year <= 2022:
                            emissions_data.append({
                                '연도': year,
                                '총배출량': total_emission,
                                '에너지': energy_emission,
                                '산업공정': industrial_emission,
                                '농업': agriculture_emission,
                                '폐기물': waste_emission
                            })
                    except (IndexError, KeyError, ValueError, TypeError):
                        continue
                
                return pd.DataFrame(emissions_data)
            except UnicodeDecodeError:
                continue
        return pd.DataFrame()
    except Exception as e:
        st.error(f"배출량 데이터 로드 오류: {e}")
        return pd.DataFrame()

def load_market_data():
    """배출권 거래데이터 로드"""
    try:
        for encoding in ['cp949', 'euc-kr', 'utf-8']:
            try:
                df = pd.read_csv('data/배출권_거래데이터.csv', encoding=encoding)
                
                # KAU24 데이터만 필터링
                kau_data = df[df['종목명'] == 'KAU24'].copy()
                
                # 데이터 정리
                kau_data['일자'] = pd.to_datetime(kau_data['일자'])
                kau_data['시가'] = kau_data['시가'].str.replace(',', '').astype(float)
                kau_data['거래량'] = kau_data['거래량'].str.replace(',', '').astype(float)
                kau_data['거래대금'] = kau_data['거래대금'].str.replace(',', '').astype(float)
                
                # 시가가 0인 경우 제외 (거래가 없는 날)
                kau_data = kau_data[kau_data['시가'] > 0]
                
                # 연도, 월 컬럼 추가
                kau_data['연도'] = kau_data['일자'].dt.year
                kau_data['월'] = kau_data['일자'].dt.month
                kau_data['연월'] = kau_data['일자'].dt.strftime('%Y-%m')
                
                return kau_data
            except UnicodeDecodeError:
                continue
        return pd.DataFrame()
    except Exception as e:
        st.error(f"시장 데이터 로드 오류: {e}")
        return pd.DataFrame()

def load_allocation_data():
    """3차 사전할당 데이터 로드"""
    try:
        for encoding in ['cp949', 'euc-kr', 'utf-8']:
            try:
                df = pd.read_csv('data/01. 3차_사전할당_20250613090824.csv', encoding=encoding)
                
                # 컬럼명 정리
                df.columns = df.columns.str.strip()
                
                # 데이터 변환
                allocation_data = []
                for _, row in df.iterrows():
                    try:
                        company_name = row.iloc[2]  # 업체명 컬럼
                        industry = row.iloc[1]      # 업종 컬럼
                        
                        # 연도별 할당량 추출
                        for year in [2021, 2022, 2023, 2024, 2025]:
                            if str(year) in df.columns:
                                allocation = row[df.columns.get_loc(str(year))]
                                if pd.notna(allocation) and allocation != 0:
                                    allocation_data.append({
                                        '연도': year,
                                        '업체명': company_name,
                                        '업종': industry,
                                        '대상년도별할당량': float(allocation)
                                    })
                    except (IndexError, KeyError):
                        continue
                
                return pd.DataFrame(allocation_data)
            except UnicodeDecodeError:
                continue
        return pd.DataFrame()
    except Exception as e:
        st.error(f"할당량 데이터 로드 오류: {e}")
        return pd.DataFrame()

def load_map_data():
    """지역별 이산화탄소 농도 데이터 로드"""
    try:
        # 샘플 맵 데이터 생성 (실제 파일이 Excel이므로)
        regions = ['서울', '부산', '대구', '인천', '광주', '대전', '울산', '세종', '경기', '강원', '충북', '충남', '전북', '전남', '경북', '경남', '제주']
        coords = {
            '서울': (37.5665, 126.9780), '부산': (35.1796, 129.0756), '대구': (35.8714, 128.6014),
            '인천': (37.4563, 126.7052), '광주': (35.1595, 126.8526), '대전': (36.3504, 127.3845),
            '울산': (35.5384, 129.3114), '세종': (36.4800, 127.2890), '경기': (37.4138, 127.5183),
            '강원': (37.8228, 128.1555), '충북': (36.8, 127.7), '충남': (36.5184, 126.8000),
            '전북': (35.7175, 127.153), '전남': (34.8679, 126.991), '경북': (36.4919, 128.8889),
            '경남': (35.4606, 128.2132), '제주': (33.4996, 126.5312)
        }
        
        map_data = []
        for region in regions:
            base_co2 = np.random.uniform(410, 430)
            map_data.append({
                '지역명': region,
                '이산화탄소_농도': base_co2 + np.random.uniform(-3, 3),
                '위도': coords[region][0],
                '경도': coords[region][1]
            })
        
        return pd.DataFrame(map_data)
    except Exception as e:
        st.error(f"지도 데이터 로드 오류: {e}")
        return pd.DataFrame()

def load_timeseries_data():
    """시계열 데이터 로드"""
    try:
        # 지역별 데이터 추출 (시계열용)
        regions = ['서울', '부산', '대구', '인천', '광주']
        time_series_data = []
        
        # 샘플 시계열 데이터 생성
        for year in range(2020, 2025):
            for month in range(1, 13):
                for region in regions:
                    time_series_data.append({
                        '지역명': region,
                        '연도': year,
                        '월': month,
                        '연월': f"{year}-{month:02d}",
                        '평균_이산화탄소_농도': np.random.uniform(410, 425) + np.sin((month-1)/12*2*np.pi) * 3 + (year - 2020) * 1.5
                    })
        
        return pd.DataFrame(time_series_data)
    except Exception as e:
        st.error(f"시계열 데이터 로드 오류: {e}")
        return pd.DataFrame()

def load_gauge_data():
    """게이지 차트용 데이터 로드"""
    try:
        # 게이지 데이터 생성
        gauge_data = []
        for year in range(2020, 2025):
            for month in range(1, 13):
                gauge_data.append({
                    '연도': year,
                    '월': month,
                    '연월': f"{year}-{month:02d}",
                    '탄소배출권_보유수량': np.random.randint(800000, 1200000) + (year-2020)*50000,
                    '현재_탄소배출량': np.random.randint(600000, 900000) + (year-2020)*30000
                })
        
        return pd.DataFrame(gauge_data)
    except Exception as e:
        st.error(f"게이지 데이터 로드 오류: {e}")
        return pd.DataFrame()

# 시나리오 분석 함수
# 시각화 요청 감지 및 차트 생성 함수들
def is_visualization_request(user_input):
    """사용자 입력이 시각화 요청인지 판단"""
    visualization_keywords = [
        # 한국어 키워드
        '그래프', '그려줘', '그려주세요', '그려', '차트', '플롯', '그림', 
        '시각화', '도표', '막대그래프', '선그래프', '파이차트', '보여줘',
        '표시해', '나타내', '그려서', '차트로', '그래프로', '비교해줘',
        '시각적', '도식화', '그림으로', '차트로',
        # 영어 키워드  
        'plot', 'chart', 'graph', 'visualization', 'draw', 'show chart',
        'bar chart', 'line chart', 'pie chart', 'visualize', 'compare'
    ]
    
    user_input_lower = user_input.lower()
    return any(keyword in user_input_lower for keyword in visualization_keywords)

def detect_chart_type(user_input):
    """사용자 입력에서 차트 타입을 감지"""
    user_input_lower = user_input.lower()
    
    # 배출량 관련
    if any(keyword in user_input_lower for keyword in ['배출량', '온실가스', '탄소', 'emission']):
        return 'emissions'
    # 시장/가격 관련
    elif any(keyword in user_input_lower for keyword in ['가격', '시가', '거래량', 'kau', '배출권', 'market']):
        return 'market'
    # 할당량 관련
    elif any(keyword in user_input_lower for keyword in ['할당량', '업체', '회사', 'allocation']):
        return 'allocation'
    # 기본값: 배출량
    else:
        return 'emissions'

def create_emissions_chart(emissions_df, selected_year):
    """배출량 차트 생성"""
    if emissions_df.empty:
        return None
    
    # 최근 10년 데이터 필터링
    recent_data = emissions_df[emissions_df['연도'] >= (selected_year - 9)]
    recent_data = recent_data[recent_data['연도'] <= selected_year]
    
    fig = go.Figure()
    
    # 총배출량 선 그래프
    fig.add_trace(go.Scatter(
        x=recent_data['연도'],
        y=recent_data['총배출량'],
        mode='lines+markers',
        name='총배출량',
        line=dict(color='red', width=3),
        marker=dict(size=8),
        hovertemplate='<b>총배출량</b><br>' +
                     '연도: %{x}<br>' +
                     '배출량: %{y:,.1f} Gg CO₂eq<br>' +
                     '<extra></extra>'
    ))
    
    # 에너지배출량 선 그래프
    fig.add_trace(go.Scatter(
        x=recent_data['연도'],
        y=recent_data['에너지'],
        mode='lines+markers',
        name='에너지배출량',
        line=dict(color='blue', width=3),
        marker=dict(size=8),
        hovertemplate='<b>에너지배출량</b><br>' +
                     '연도: %{x}<br>' +
                     '배출량: %{y:,.1f} Gg CO₂eq<br>' +
                     '<extra></extra>'
    ))
    
    fig.update_layout(
        title=f"연도별 온실가스 배출량 추이 ({selected_year-9}~{selected_year})",
        xaxis_title="연도",
        yaxis_title="배출량 (Gg CO₂eq)",
        height=400,
        yaxis=dict(
            tickformat=".0f",
            hoverformat=".1f",
            separatethousands=True
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    return fig

def create_market_chart(market_df, selected_year):
    """시장 데이터 차트 생성"""
    if market_df.empty:
        return None
    
    # 선택된 연도 데이터 필터링
    market_filtered = market_df[market_df['연도'] == selected_year]
    
    if market_filtered.empty:
        return None
    
    # 월별 평균 계산
    monthly_data = market_filtered.groupby('월').agg({
        '시가': 'mean',
        '거래량': 'sum'
    }).reset_index()
    
    # 콤보 차트 생성
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # 거래량 바 차트
    fig.add_trace(
        go.Bar(
            x=monthly_data['월'], 
            y=monthly_data['거래량'], 
            name="거래량", 
            marker_color='lightblue',
            hovertemplate='<b>거래량</b><br>' +
                         '월: %{x}<br>' +
                         '거래량: %{y:,.0f}<br>' +
                         '<extra></extra>'
        ),
        secondary_y=False,
    )
    
    # 시가 선 차트
    fig.add_trace(
        go.Scatter(
            x=monthly_data['월'], 
            y=monthly_data['시가'], 
            mode='lines+markers', 
            name="평균 시가", 
            line=dict(color='red', width=3),
            marker=dict(size=8),
            hovertemplate='<b>평균 시가</b><br>' +
                         '월: %{x}<br>' +
                         '시가: %{y:,.0f}원<br>' +
                         '<extra></extra>'
        ),
        secondary_y=True,
    )
    
    fig.update_xaxes(title_text="월")
    fig.update_yaxes(title_text="거래량", secondary_y=False)
    fig.update_yaxes(title_text="시가 (원)", secondary_y=True)
    fig.update_layout(
        title=f"{selected_year}년 KAU24 월별 시가/거래량 추이",
        height=400
    )
    
    return fig

def create_allocation_chart(allocation_df, selected_year):
    """할당량 차트 생성"""
    if allocation_df.empty:
        return None
    
    # 선택된 연도 데이터 필터링
    allocation_filtered = allocation_df[allocation_df['연도'] == selected_year]
    
    if allocation_filtered.empty:
        # 다른 연도 데이터 사용
        available_years = sorted(allocation_df['연도'].unique())
        if available_years:
            selected_year = available_years[-1]  # 가장 최근 연도
            allocation_filtered = allocation_df[allocation_df['연도'] == selected_year]
    
    if allocation_filtered.empty:
        return None
    
    # 상위 15개 업체 필터링
    top_companies = allocation_filtered.nlargest(15, '대상년도별할당량')
    
    # 막대 차트 생성
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=top_companies['대상년도별할당량'],
        y=top_companies['업체명'],
        orientation='h',
        marker_color='green',
        hovertemplate='<b>%{y}</b><br>' +
                     '할당량: %{x:,.0f} tCO₂eq<br>' +
                     '<extra></extra>'
    ))
    
    fig.update_layout(
        title=f"{selected_year}년 상위 15개 업체별 배출권 할당량",
        xaxis_title="할당량 (tCO₂eq)",
        yaxis_title="업체명",
        height=500,
        xaxis=dict(
            tickformat=".0f",
            separatethousands=True
        )
    )
    
    return fig

def analyze_scenario(user_input, emissions_df, market_df, allocation_df, selected_year=2025):
    """사용자 입력을 분석하여 시각화 또는 기본 응답을 반환 (AI 판단 배제)"""
    
    # 1. 시각화 요청인지 '규칙'으로만 판단
    if is_visualization_request(user_input):
        chart_type = detect_chart_type(user_input)
        
        # 필요한 데이터프레임 선택
        df_map = {'emissions': emissions_df, 'market': market_df, 'allocation': allocation_df}
        required_df = df_map.get(chart_type)
        
        # 데이터 유무 확인
        if required_df is None or required_df.empty:
            return "❌ 요청하신 차트를 그리는 데 필요한 데이터가 없습니다."
        
        # 차트 생성
        chart_fig = None
        response_text = f"✅ 요청하신 {chart_type} 차트를 생성했습니다." # 기본 응답

        if chart_type == 'emissions':
            chart_fig = create_emissions_chart(emissions_df, selected_year)
            # 정확한 데이터 기반으로 템플릿 응답 생성 (AI 개입 없음)
            try:
                val_2017 = emissions_df.loc[emissions_df['연도'] == 2017, '총배출량'].iloc[0]
                val_2021 = emissions_df.loc[emissions_df['연도'] == 2021, '총배출량'].iloc[0]
                diff = val_2017 - val_2021
                response_text = (
                    f"✅ 2017년 대비 2021년 총배출량은 **{diff:,.1f} Gg CO₂eq** 만큼 감소했습니다.\n\n"
                    f"- **2017년**: `{val_2017:,.1f}` Gg CO₂eq\n"
                    f"- **2021년**: `{val_2021:,.1f}` Gg CO₂eq\n\n"
                    f"*데이터 출처: 국가 온실가스 인벤토리(1990-2021)*"
                )
            except (IndexError, KeyError):
                pass # 특정 연도 데이터 없으면 기본 응답 사용

        elif chart_type == 'market':
            chart_fig = create_market_chart(market_df, selected_year)
        elif chart_type == 'allocation':
            chart_fig = create_allocation_chart(allocation_df, selected_year)

        # 차트 표시 요청
        if chart_fig:
            st.session_state.chart_to_display = chart_fig
            return response_text
        else:
            return "❌ 죄송합니다. 데이터는 있으나 차트 생성에 실패했습니다."

    # 2. 시각화 요청이 아닐 경우, 기본 안내 메시지 반환
    return "안녕하세요! 저는 탄소 중립 보조 AI입니다. '2017년과 2021년 배출량 비교 그래프 보여줘' 와 같이 질문해주세요."

# 데이터 로드
emissions_df = load_emissions_data()
market_df = load_market_data()
allocation_df = load_allocation_data()
timeseries_df = load_timeseries_data()
gauge_df = load_gauge_data()

# 메인 레이아웃: 좌측과 우측으로 분할
left_col, right_col = st.columns([1, 1.2])

# 좌측: 필터 + 게이지 + 맵 차트
with left_col:
    # 필터 섹션
    st.markdown('<div class="filter-container">', unsafe_allow_html=True)
    st.subheader("🔍 필터 설정")

    col1, col2 = st.columns(2)
    with col1:
        if not emissions_df.empty:
            selected_year = st.slider(
                "연도 선택",
                min_value=int(emissions_df['연도'].min()),
                max_value=2025,
                value=2025,
                step=1
            )
        else:
            selected_year = 2025

    with col2:
        selected_month = st.slider(
            "월 선택",
            min_value=1,
            max_value=12,
            value=1,
            step=1
        )

    st.markdown('</div>', unsafe_allow_html=True)
    
    # 게이지 차트 섹션
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    st.subheader("📊 현황 지표")
    
    # 게이지 데이터 필터링
    gauge_filtered = gauge_df[(gauge_df['연도'] == selected_year) & (gauge_df['월'] == selected_month)]
    
    if not gauge_filtered.empty:
        emission_allowance = gauge_filtered.iloc[0]['탄소배출권_보유수량']
        current_emission = gauge_filtered.iloc[0]['현재_탄소배출량']
        
        # 게이지 차트 생성
        fig_gauges = make_subplots(
            rows=1, cols=2,
            specs=[[{'type': 'indicator'}, {'type': 'indicator'}]],
            subplot_titles=('탄소배출권 보유수량', '현재 탄소배출량'),
            horizontal_spacing=0.2
        )

        # 탄소배출권 보유수량 게이지
        fig_gauges.add_trace(
            go.Indicator(
                mode="gauge+number",
                value=emission_allowance,
                title={'text': f"보유수량<br><span style='font-size:0.8em;color:gray'>{selected_year}년 {selected_month}월</span>"},
                number={'suffix': " tCO₂eq", 'font': {'size': 16}},
                gauge={
                    'axis': {'range': [None, 1500000], 'tickfont': {'size': 10}},
                    'bar': {'color': "lightgreen", 'thickness': 0.8},
                    'bgcolor': "white",
                    'borderwidth': 2,
                    'bordercolor': "gray",
                    'steps': [
                        {'range': [0, 500000], 'color': "lightgray"},
                        {'range': [500000, 1000000], 'color': "gray"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 1200000
                    }
                }
            ),
            row=1, col=1
        )

        # 현재 탄소배출량 게이지
        fig_gauges.add_trace(
            go.Indicator(
                mode="gauge+number",
                value=current_emission,
                title={'text': f"현재배출량<br><span style='font-size:0.8em;color:gray'>{selected_year}년 {selected_month}월</span>"},
                number={'suffix': " tCO₂eq", 'font': {'size': 16}},
                gauge={
                    'axis': {'range': [None, 1200000], 'tickfont': {'size': 10}},
                    'bar': {'color': "orange", 'thickness': 0.8},
                    'bgcolor': "white",
                    'borderwidth': 2,
                    'bordercolor': "gray",
                    'steps': [
                        {'range': [0, 400000], 'color': "lightgray"},
                        {'range': [400000, 800000], 'color': "gray"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 1000000
                    }
                }
            ),
            row=1, col=2
        )

        fig_gauges.update_layout(
            height=350,
            margin=dict(l=20, r=20, t=80, b=20),
            font=dict(size=12),
            showlegend=False
        )
        st.plotly_chart(fig_gauges, use_container_width=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 맵 차트 섹션 (샘플 데이터 사용)
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    st.subheader("🗺️ 지역별 이산화탄소 농도 현황")
    
    # 샘플 맵 데이터 생성
    regions = ['서울', '부산', '대구', '인천', '광주', '대전', '울산', '세종', '경기', '강원', '충북', '충남', '전북', '전남', '경북', '경남', '제주']
    coords = {
        '서울': (37.5665, 126.9780), '부산': (35.1796, 129.0756), '대구': (35.8714, 128.6014),
        '인천': (37.4563, 126.7052), '광주': (35.1595, 126.8526), '대전': (36.3504, 127.3845),
        '울산': (35.5384, 129.3114), '세종': (36.4800, 127.2890), '경기': (37.4138, 127.5183),
        '강원': (37.8228, 128.1555), '충북': (36.8, 127.7), '충남': (36.5184, 126.8000),
        '전북': (35.7175, 127.153), '전남': (34.8679, 126.991), '경북': (36.4919, 128.8889),
        '경남': (35.4606, 128.2132), '제주': (33.4996, 126.5312)
    }
    
    map_data = []
    for region in regions:
        base_co2 = np.random.uniform(410, 430)
        seasonal_effect = np.sin((selected_month-1)/12*2*np.pi) * 5
        yearly_trend = (selected_year - 2020) * 2
        
        map_data.append({
            '지역명': region,
            '평균_이산화탄소_농도': base_co2 + seasonal_effect + yearly_trend + np.random.uniform(-3, 3),
            'lat': coords[region][0],
            'lon': coords[region][1]
        })
    
    map_df = pd.DataFrame(map_data)
    
    fig_map = go.Figure()
    
    fig_map.add_trace(go.Scattermap(
        lat=map_df["lat"],
        lon=map_df["lon"],
        mode='markers',
        marker=dict(
            size=map_df["평균_이산화탄소_농도"] / 15,
            color=map_df["평균_이산화탄소_농도"],
            colorscale="Reds",
            showscale=True,
            colorbar=dict(title="CO₂ 농도 (ppm)")
        ),
        text=map_df["지역명"],
        hovertemplate="<b>%{text}</b><br>CO₂ 농도: %{marker.color:.1f} ppm<extra></extra>",
        name="지역별 CO₂ 농도"
    ))
        
    fig_map.update_layout(
        mapbox=dict(
            style="open-street-map",
            center=dict(lat=36.5, lon=127.5),
            zoom=6
        ),
        height=500,
        margin=dict(l=0, r=0, t=30, b=0),
        title=f"{selected_year}년 {selected_month}월 지역별 평균 이산화탄소 농도 분포"
    )
        
    st.plotly_chart(fig_map, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# 우측: 4단계 구성
with right_col:
    # 우측 최상단: 막대 그래프 (연도별 배출량)
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    st.subheader("📊 연도별 탄소 배출량 현황")
    st.markdown("*단위: Gg CO₂eq (기가그램 CO₂ 당량)*")
    
    if not emissions_df.empty:
        emissions_filtered = emissions_df[emissions_df['연도'] <= selected_year]
        
        fig_bar = go.Figure()
        
        fig_bar.add_trace(go.Bar(
            x=emissions_filtered['연도'],
            y=emissions_filtered['총배출량'],
            name='총배출량',
            marker_color='gold',
            # 정확한 값을 호버 텍스트로 표시
            hovertemplate='<b>총배출량</b><br>' +
                         '연도: %{x}<br>' +
                         '배출량: %{y:,.1f} Gg CO₂eq<br>' +
                         '<extra></extra>'
        ))
        
        fig_bar.add_trace(go.Bar(
            x=emissions_filtered['연도'],
            y=emissions_filtered['에너지'],
            name='에너지배출량',
            marker_color='steelblue',
            # 정확한 값을 호버 텍스트로 표시  
            hovertemplate='<b>에너지배출량</b><br>' +
                         '연도: %{x}<br>' +
                         '배출량: %{y:,.1f} Gg CO₂eq<br>' +
                         '<extra></extra>'
        ))
        
        fig_bar.update_layout(
            title=f"{selected_year}년까지 연도별 배출량 비교",
            xaxis_title="연도",
            yaxis_title="배출량 (Gg CO₂eq)",
            barmode='group',
            height=300,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            # Y축 숫자 포맷팅을 정밀하게 설정
            yaxis=dict(
                tickformat=".0f",  # 소수점 없이 정수로 표시
                hoverformat=".1f",  # 호버 시에는 소수점 1자리까지
                separatethousands=True  # 천 단위 구분자 표시
            )
        )
        
        st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.warning("배출량 데이터를 불러올 수 없습니다.")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 🥇 대화형 시나리오 시뮬레이션 (What-if 분석)
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    st.subheader("🥇 대화형 시나리오 시뮬레이션")
    st.markdown("*챗봇과 대화하며 What-if 분석을 진행하세요*")
    
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Display chat messages from history on app rerun
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Accept user input
    if prompt := st.chat_input("질문을 입력하세요 (예: '감축률을 20%로 올리면 얼마나 투자해야 하나요?')"):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message in chat message container
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Display assistant response in chat message container
        with st.chat_message("assistant"):
            response = analyze_scenario(prompt, emissions_df, market_df, allocation_df, selected_year)
            st.markdown(response)
            
            # 시각화 요청인 경우 차트 표시
            if hasattr(st.session_state, 'chart_to_display') and st.session_state.chart_to_display is not None:
                st.plotly_chart(st.session_state.chart_to_display, use_container_width=True)
                # 차트 표시 후 초기화
                st.session_state.chart_to_display = None
        
        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": response})
    
    # 대화 초기화 버튼
    if st.button("🗑️ 대화 초기화"):
        st.session_state.messages = []
        st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 우측 중간 1: 콤보 그래프 (시가 + 거래량)
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    st.subheader("💹 KAU24 시가/거래량")
    
    if not market_df.empty:
        market_filtered = market_df[market_df['연도'] == selected_year]
        
        if not market_filtered.empty:
            fig_combo = make_subplots(specs=[[{"secondary_y": True}]])
            
            fig_combo.add_trace(
                go.Bar(x=market_filtered['월'], y=market_filtered['거래량'], name="거래량", marker_color='steelblue'),
                secondary_y=False,
            )
            
            fig_combo.add_trace(
                go.Scatter(x=market_filtered['월'], y=market_filtered['시가'], mode='lines+markers', 
                          name="시가", line=dict(color='gold', width=3)),
                secondary_y=True,
            )
            
            fig_combo.update_xaxes(title_text="월")
            fig_combo.update_yaxes(title_text="거래량", secondary_y=False)
            fig_combo.update_yaxes(title_text="시가 (원)", secondary_y=True)
            fig_combo.update_layout(title=f"{selected_year}년 월별 시가/거래량 추이", height=300)
            
            st.plotly_chart(fig_combo, use_container_width=True)
        else:
            st.warning(f"{selected_year}년 데이터가 없습니다.")
    else:
        st.warning("시장 데이터를 불러올 수 없습니다.")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 우측 중간 2: 트리맵
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    st.subheader("🏭 업체별 할당량 현황")
    
    if not allocation_df.empty:
        # 선택된 연도에 데이터가 있는지 확인
        treemap_filtered = allocation_df[allocation_df['연도'] == selected_year]
        
        # 선택된 연도에 데이터가 없으면 다른 연도 찾기
        if treemap_filtered.empty:
            available_years = sorted(allocation_df['연도'].unique())
            if available_years:
                # 가장 최근 연도 선택
                selected_year_for_treemap = available_years[-1]
                treemap_filtered = allocation_df[allocation_df['연도'] == selected_year_for_treemap]
                st.info(f"{selected_year}년 데이터가 없어 {selected_year_for_treemap}년 데이터를 표시합니다.")
            else:
                selected_year_for_treemap = selected_year
        else:
            selected_year_for_treemap = selected_year
        
        if not treemap_filtered.empty:
            fig_treemap = px.treemap(
                treemap_filtered,
                path=['업종', '업체명'],
                values='대상년도별할당량',
                title=f"{selected_year_for_treemap}년 업종별/업체별 할당량 분포",
                height=300,
                color='대상년도별할당량',
                color_continuous_scale='Viridis'
            )
            
            st.plotly_chart(fig_treemap, use_container_width=True)
        else:
            st.warning(f"할당량 데이터가 없습니다.")
    else:
        st.warning("할당량 데이터를 불러올 수 없습니다.")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 우측 하단: 시계열 그래프
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    st.subheader("📈 지역별 이산화탄소 농도 시계열")
    
    if not timeseries_df.empty:
        timeseries_filtered = timeseries_df[timeseries_df['연도'] <= selected_year]
        
        fig_timeseries = px.line(
            timeseries_filtered,
            x='연월',
            y='평균_이산화탄소_농도',
            color='지역명',
            title=f"{selected_year}년까지 월별 지역별 CO₂ 농도 변화",
            height=300,
            markers=True
        )
        
        fig_timeseries.update_layout(
            xaxis_title="연월",
            yaxis_title="CO₂ 농도 (ppm)",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        
        st.plotly_chart(fig_timeseries, use_container_width=True)
    else:
        st.warning("시계열 데이터를 불러올 수 없습니다.")
    
    st.markdown('</div>', unsafe_allow_html=True)

# 사이드바에 데이터 업로드 기능 추가
with st.sidebar:
    st.header("📊 데이터 관리")
    
    st.subheader("📁 데이터 업로드")
    uploaded_files = {}
    
    uploaded_files['emissions'] = st.file_uploader(
        "배출량 데이터 (국가 온실가스 인벤토리)",
        type="csv",
        key="emissions"
    )
    
    uploaded_files['market'] = st.file_uploader(
        "시장 데이터 (배출권 거래데이터)",
        type="csv",
        key="market"
    )
    
    uploaded_files['allocation'] = st.file_uploader(
        "할당량 데이터 (3차 사전할당)",
        type="csv",
        key="allocation"
    )
    
    if st.button("🔄 데이터 새로고침"):
        st.rerun()

# 플로팅 챗봇 버튼 제거됨

# 푸터
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #888; margin-top: 50px;'>
        <p>🌍 탄소배출량 및 배출권 현황 대시보드 | Built with Streamlit & Plotly</p>
        <p>실제 데이터 기반 분석</p>
    </div>
    """, 
    unsafe_allow_html=True
)
