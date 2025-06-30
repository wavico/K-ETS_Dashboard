"""
Streamlit 최적화 탄소 데이터 분석 에이전트
- 간결하고 유지보수 가능한 단일 파일 구조
- 깔끔한 답변과 그래프 표시
- 쿼리문 숨김 처리
"""

import os
import io
import sys
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import seaborn as sns
from pathlib import Path
from typing import Tuple, Optional, Dict, Any
from dotenv import load_dotenv
from matplotlib.ticker import FuncFormatter
import numpy as np

# LangChain imports
try:
    from langchain_upstage import ChatUpstage
    UPSTAGE_AVAILABLE = True
except ImportError:
    from langchain_openai import ChatOpenAI
    UPSTAGE_AVAILABLE = False

# 환경변수 로드
load_dotenv()


class EnhancedCarbonRAGAgent:
    """Streamlit에 최적화된 간결한 탄소 데이터 분석 에이전트"""
    
    def __init__(self, data_folder: str = "data"):
        """
        Args:
            data_folder: CSV 파일들이 있는 폴더 경로
        """
        self.data_folder = Path(data_folder)
        self.df = None
        self.llm = None
        self._setup_korean_font()
        self._load_data()
        self._setup_llm()
    
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
                    print(f"✅ 한글 폰트 설정 성공: {font_prop.get_name()}")
                    break
        except Exception as e:
            print(f"⚠️ 한글 폰트 설정 실패: {e}")
    
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
                            print(f"✅ 로드 성공: {filename} ({df.shape})")
                            break
                        except UnicodeDecodeError:
                            continue
                    else:
                        print(f"❌ 로드 실패: {filename}")
            
            # 통합 DataFrame 생성
            if dataframes:
                self.df = pd.concat(dataframes, ignore_index=True, sort=False)
                print(f"📊 통합 데이터: {self.df.shape}")
                
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
            print(f"❌ 데이터 로드 오류: {e}")
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
                                print(f"✅ 연도 컬럼 '{col}' 정수로 변환 완료")
                            else:
                                self.column_types[col] = 'string_year'
                                print(f"⚠️ 연도 컬럼 '{col}' 문자열로 유지")
                        else:
                            # 숫자 타입인 경우 소수점 제거
                            try:
                                # float 타입인 경우 정수로 변환
                                if self.df[col].dtype in ['float64', 'float32']:
                                    self.df[col] = self.df[col].astype('Int64')
                                    print(f"✅ 연도 컬럼 '{col}' 소수점 제거하여 정수로 변환 완료")
                                else:
                                    print(f"✅ 연도 컬럼 '{col}' 이미 정수 타입")
                                self.column_types[col] = 'numeric_year'
                            except Exception as conv_error:
                                print(f"⚠️ 연도 컬럼 '{col}' 정수 변환 실패: {conv_error}")
                                self.column_types[col] = 'numeric_year'
                            
                except Exception as e:
                    self.column_types[col] = 'unknown_year'
                    print(f"⚠️ 연도 컬럼 '{col}' 타입 분석 실패: {e}")
            
            # 기타 컬럼 타입 저장
            elif col not in self.column_types:
                dtype = str(self.df[col].dtype)
                self.column_types[col] = dtype
        
        print(f"📊 연도 컬럼 발견: {self.year_columns}")
        print(f"📊 컬럼 타입 정보: {len(self.column_types)}개 컬럼 분석 완료")
    
    def _setup_llm(self):
        """LLM 초기화"""
        try:
            # API 키 확인
            if UPSTAGE_AVAILABLE and os.getenv('UPSTAGE_API_KEY'):
                self.llm = ChatUpstage(
                    model="solar-mini-250422",
                    temperature=0,
                    api_key=os.getenv('UPSTAGE_API_KEY')
                )
                print("✅ Upstage LLM 초기화 완료")
            elif os.getenv('OPENAI_API_KEY'):
                self.llm = ChatOpenAI(
                    model="gpt-3.5-turbo",
                    temperature=0,
                    api_key=os.getenv('OPENAI_API_KEY')
                )
                print("✅ OpenAI LLM 초기화 완료")
            else:
                raise ValueError("API 키가 설정되지 않았습니다. .env 파일을 확인해주세요.")
                
        except Exception as e:
            print(f"❌ LLM 초기화 실패: {e}")
            self.llm = None
    
    def _generate_code(self, question: str) -> str:
        """질문을 분석하여 Python 코드 생성"""
        if not self.llm:
            return None
        
        # 데이터 정보 제공
        columns_info = ', '.join(self.df.columns[:10].tolist())
        data_shape = self.df.shape
        
        # 샘플 데이터 미리보기
        sample_data = self.df.head(3).to_string()
        
        # 데이터 소스별 정보 생성
        datasource_info = ""
        if '데이터소스' in self.df.columns:
            source_counts = self.df['데이터소스'].value_counts()
            datasource_details = []
            for source, count in source_counts.items():
                datasource_details.append(f"  - {source}: {count}행")
            datasource_info = f"""
**📊 데이터 소스별 행 수 (총 {self.df.shape[0]}행):**
{chr(10).join(datasource_details)}
"""
        
        # 연도 컬럼 정보 생성
        year_info = ""
        if hasattr(self, 'year_columns') and self.year_columns:
            year_details = []
            for col in self.year_columns:
                col_type = getattr(self, 'column_types', {}).get(col, 'unknown')
                sample_vals = self.df[col].dropna().head(3).tolist()
                year_details.append(f"  - '{col}': {col_type} 타입, 샘플값: {sample_vals}")
            year_info = f"""
**연도 관련 컬럼:**
{chr(10).join(year_details)}
"""
        
        prompt = f"""
당신은 탄소 배출 데이터 분석 전문가입니다. 다음 질문에 대해 적절한 Python 코드를 생성하세요.

## ⚠️ 중요: 통합 데이터 정보
- 데이터프레임 변수명: df
- **전체 데이터 크기: {data_shape[0]}행 {data_shape[1]}열** 
- 이는 여러 CSV 파일을 통합한 결과입니다
- 주요 컬럼: {columns_info}

{datasource_info}

## 중요한 데이터 구조 정보
{year_info}

## 샘플 데이터 미리보기
{sample_data}

## 질문
{question}

## 질문 유형 분류 및 대응 방법

### 1️⃣ 단답형 질문 (그래프/테이블 불필요)
**패턴**: "몇 개", "가장 높은/낮은", "언제", "얼마", "차이는", "평균은", "행이", "데이터" 등
**대응**: 계산 결과를 result 변수에 문자열로 저장, table_result = None

**예시질문 1**: "데이터에 몇 개의 행이 있어?"
```python
# 전체 데이터 행 수 확인 (통합된 모든 데이터)
total_rows = len(df)
result = f"전체 통합 데이터에는 {{total_rows:,}}개의 행이 있습니다."
table_result = None
```

**예시질문 2**: "데이터는 몇 행이야?"
```python
# 전체 데이터 행 수 확인
total_rows = df.shape[0]
result = f"데이터는 총 {{total_rows:,}}행입니다."
table_result = None
```
  
**예시질문 3**: "가장 배출량이 높은 연도는 언제인가요?"
```python
# 1단계: NA 값 제거
df_clean = df.dropna(subset=['분야 및 연도', '총배출량(kt CO2-eq)'])

# 2단계: 최대값 찾기 및 추가 분석
max_year = df_clean.loc[df_clean['총배출량(kt CO2-eq)'].idxmax(), '분야 및 연도']
max_value = df_clean['총배출량(kt CO2-eq)'].max()
avg_value = df_clean['총배출량(kt CO2-eq)'].mean()

# 3단계: 결과 문자열 생성 (구체적인 수치로 예시 제공)
result = "가장 배출량이 높은 연도는 2021년이며, 배출량은 1,234,567 kt CO2-eq입니다. 이는 평균 배출량(987,654 kt CO2-eq)보다 246,913 kt CO2-eq 높은 수치입니다."
table_result = None
```

**예시질문 2**: "총 배출량의 평균은 얼마인가요?"
```python
# 1단계: NA 값 제거
df_clean = df.dropna(subset=['총배출량(kt CO2-eq)'])

# 2단계: 평균 계산 및 추가 통계
avg_value = df_clean['총배출량(kt CO2-eq)'].mean()
min_value = df_clean['총배출량(kt CO2-eq)'].min()
max_value = df_clean['총배출량(kt CO2-eq)'].max()
count = len(df_clean)

# 3단계: 결과 문자열 생성
result = "총 배출량의 평균은 987,654 kt CO2-eq입니다. 최솟값 456,789 kt CO2-eq, 최댓값 1,234,567 kt CO2-eq이며, 총 15개 연도의 데이터를 기준으로 계산되었습니다."
table_result = None
```

**예시질문 3**: "2020년과 2021년의 배출량 차이는 얼마인가요?"
```python
# 1단계: NA 값 제거
df_clean = df.dropna(subset=['분야 및 연도', '총배출량(kt CO2-eq)'])

# 2단계: 특정 연도 데이터 추출
data_2020 = df_clean[df_clean['분야 및 연도'] == 2020]['총배출량(kt CO2-eq)'].iloc[0]
data_2021 = df_clean[df_clean['분야 및 연도'] == 2021]['총배출량(kt CO2-eq)'].iloc[0]
difference = data_2021 - data_2020
percent_change = (difference / data_2020) * 100

# 3단계: 결과 문자열 생성
result = "2020년과 2021년의 배출량 차이는 45,678 kt CO2-eq입니다. 2020년 1,189,123 kt CO2-eq에서 2021년 1,234,801 kt CO2-eq로 3.8% 증가했습니다."
table_result = None
```

### 2️⃣ 추세 그래프 질문 (라인 그래프 - 총배출량)
**패턴**: "변화", "추이", "트렌드", "패턴", "흐름", "최근 N년간", "시간에 따른", "총배출량" 등
**대응**: 총배출량을 사용한 라인 그래프 생성 + 설명

**예시질문 1**: "최근 5년간의 배출량 추이는 어떤가요?"
```python
# 1단계: NA 값 제거 (필수)
df_clean = df.dropna(subset=['분야 및 연도', '총배출량(kt CO2-eq)'])

# 2단계: 최근 5년 데이터 필터링 및 중복 제거
recent_data = df_clean[df_clean['분야 및 연도'] >= 2018]
df_plot = recent_data.drop_duplicates(subset=['분야 및 연도']).sort_values('분야 및 연도')

# 3단계: 라인 그래프 생성
plt.figure(figsize=(11, 7), dpi=100)
plt.plot(df_plot['분야 및 연도'], df_plot['총배출량(kt CO2-eq)'], marker='o', linewidth=2, markersize=4)
plt.title('최근 5년간 총 배출량 변화 추세', fontsize=14, fontweight='bold')
plt.xlabel('연도', fontsize=10)
plt.ylabel('총배출량 (kt CO2-eq)', fontsize=10)

# 4단계: X축 연도 설정
unique_years = sorted(df_plot['분야 및 연도'].unique())
plt.xticks(unique_years, [str(int(year)) for year in unique_years])
plt.gca().xaxis.set_major_formatter(FuncFormatter(lambda val, pos: str(int(val))))

plt.grid(True, alpha=0.3)
plt.tight_layout()

# 5단계: 결과 설명 생성
result = "2018-2022년 총 배출량 변화 추세를 라인 그래프로 생성했습니다. 2018년 1,189,456 kt CO2-eq에서 2022년 1,234,567 kt CO2-eq로 총 +45,111 kt CO2-eq (+3.8%) 변화했습니다."
table_result = None
```

**예시질문 2**: "연도별 총 배출량 변화를 그래프로 보여주세요"
```python
# 1단계: NA 값 제거 (필수)
df_clean = df.dropna(subset=['분야 및 연도', '총배출량(kt CO2-eq)'])

# 2단계: 데이터 중복 제거 및 정렬
df_plot = df_clean.drop_duplicates(subset=['분야 및 연도']).sort_values('분야 및 연도')

# 3단계: 라인 그래프 생성
plt.figure(figsize=(11, 7), dpi=100)
plt.plot(df_plot['분야 및 연도'], df_plot['총배출량(kt CO2-eq)'], marker='o', linewidth=2, markersize=4, color='#2E86AB')
plt.title('연도별 총 배출량 변화 추세', fontsize=14, fontweight='bold')
plt.xlabel('연도', fontsize=10)
plt.ylabel('총배출량 (kt CO2-eq)', fontsize=10)

# 4단계: X축 연도 설정
unique_years = sorted(df_plot['분야 및 연도'].unique())
plt.xticks(unique_years, [str(int(year)) for year in unique_years])

plt.grid(True, alpha=0.3)
plt.tight_layout()

# 5단계: 결과 설명 생성
result = "전체 기간(2017-2022년) 총 배출량 변화 추세를 라인 그래프로 생성했습니다. 2017년 1,156,789 kt CO2-eq에서 2022년 1,234,567 kt CO2-eq로 총 +77,778 kt CO2-eq (+6.7%) 증가했습니다."
table_result = None
```

**예시질문 3**: "배출량이 증가하는 추세인가요?"
```python
# 1단계: NA 값 제거 (필수)
df_clean = df.dropna(subset=['분야 및 연도', '총배출량(kt CO2-eq)'])

# 2단계: 데이터 중복 제거 및 정렬
df_plot = df_clean.drop_duplicates(subset=['분야 및 연도']).sort_values('분야 및 연도')

# 3단계: 라인 그래프 생성
plt.figure(figsize=(11, 7), dpi=100)
plt.plot(df_plot['분야 및 연도'], df_plot['총배출량(kt CO2-eq)'], marker='o', linewidth=2, markersize=4, color='#A23B72')
plt.title('총 배출량 증감 추세 분석', fontsize=14, fontweight='bold')
plt.xlabel('연도', fontsize=10)
plt.ylabel('총배출량 (kt CO2-eq)', fontsize=10)

# 4단계: X축 연도 설정 및 추세선 추가
unique_years = sorted(df_plot['분야 및 연도'].unique())
plt.xticks(unique_years, [str(int(year)) for year in unique_years])

# 추세선 추가
z = np.polyfit(df_plot['분야 및 연도'], df_plot['총배출량(kt CO2-eq)'], 1)
p = np.poly1d(z)
plt.plot(df_plot['분야 및 연도'], p(df_plot['분야 및 연도']), "--", alpha=0.7, color='red')

plt.grid(True, alpha=0.3)
plt.tight_layout()

# 5단계: 결과 설명 생성
result = "배출량 증감 추세를 라인 그래프로 분석했습니다. 전체적으로 증가 추세를 보이며, 연평균 약 15,556 kt CO2-eq씩 증가하고 있습니다. 빨간 점선은 추세선을 나타냅니다."
table_result = None
```

### 3️⃣ 비교 그래프 질문 (막대 그래프)
**패턴**: "비교", "차이", "대비", "vs", "중 어느", "어느 것이", "A년과 B년", "특정 연도들" 등
**대응**: 막대 그래프 생성 + 설명

**예시질문 1**: "2017년과 2021년의 배출량 차이를 그래프로 비교해줘"
```python
# 1단계: NA 값 제거 (필수)
df_clean = df.dropna(subset=['분야 및 연도', '총배출량(kt CO2-eq)'])

# 2단계: 비교할 연도들 지정 및 데이터 필터링
years_to_compare = [2017, 2021]
comparison_data = df_clean[df_clean['분야 및 연도'].isin(years_to_compare)]
comparison_data = comparison_data.drop_duplicates(subset=['분야 및 연도']).sort_values('분야 및 연도')

# 3단계: 막대 그래프 생성
plt.figure(figsize=(11, 7), dpi=100)
bars = plt.bar(comparison_data['분야 및 연도'], comparison_data['총배출량(kt CO2-eq)'], 
               color=['#3498db', '#e74c3c'], alpha=0.8, width=0.6)
plt.title('2017년과 2021년 배출량 비교', fontsize=14, fontweight='bold')
plt.xlabel('연도', fontsize=10)
plt.ylabel('총배출량 (kt CO2-eq)', fontsize=10)

# 4단계: X축 연도 설정 및 값 표시
plt.xticks(comparison_data['분야 및 연도'], [str(int(year)) + '년' for year in comparison_data['분야 및 연도']])
for bar, value in zip(bars, comparison_data['총배출량(kt CO2-eq)']):
    plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + value*0.01, 
             str(int(value/1000)) + 'K', ha='center', va='bottom', fontsize=9)

plt.grid(True, alpha=0.3, axis='y')
plt.tight_layout()

# 5단계: 결과 설명 생성
result = "2017년과 2021년의 배출량을 막대 그래프로 비교했습니다. 2017년 1,156,789 kt CO2-eq에서 2021년 1,201,456 kt CO2-eq로 +44,667 kt CO2-eq (+3.9%) 증가했습니다."
table_result = None
```

**예시질문 2**: "2020년 vs 2021년 배출량 차이는?"
```python
# 1단계: NA 값 제거 (필수)
df_clean = df.dropna(subset=['분야 및 연도', '총배출량(kt CO2-eq)'])

# 2단계: 비교할 연도들 지정 및 데이터 필터링
years_to_compare = [2020, 2021]
comparison_data = df_clean[df_clean['분야 및 연도'].isin(years_to_compare)]
comparison_data = comparison_data.drop_duplicates(subset=['분야 및 연도']).sort_values('분야 및 연도')

# 3단계: 막대 그래프 생성
plt.figure(figsize=(11, 7), dpi=100)
bars = plt.bar(comparison_data['분야 및 연도'], comparison_data['총배출량(kt CO2-eq)'], 
               color=['#FF6B6B', '#4ECDC4'], alpha=0.8, width=0.5)
plt.title('2020년 대 2021년 배출량 비교', fontsize=14, fontweight='bold')
plt.xlabel('연도', fontsize=10)
plt.ylabel('총배출량 (kt CO2-eq)', fontsize=10)

# 4단계: X축 연도 설정 및 값 표시
plt.xticks(comparison_data['분야 및 연도'], [str(int(year)) + '년' for year in comparison_data['분야 및 연도']])
for bar, value in zip(bars, comparison_data['총배출량(kt CO2-eq)']):
    plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + value*0.01, 
             str(int(value/1000)) + 'K', ha='center', va='bottom', fontsize=9)

plt.grid(True, alpha=0.3, axis='y')
plt.tight_layout()

# 5단계: 결과 설명 생성
result = "2020년과 2021년의 배출량을 막대 그래프로 비교했습니다. 2020년 1,189,123 kt CO2-eq에서 2021년 1,201,456 kt CO2-eq로 +12,333 kt CO2-eq (+1.0%) 소폭 증가했습니다."
table_result = None
```

**예시질문 3**: "어느 연도가 배출량이 가장 높았나요? 비교 그래프로 보여주세요"
```python
# 1단계: NA 값 제거 (필수)
df_clean = df.dropna(subset=['분야 및 연도', '총배출량(kt CO2-eq)'])

# 2단계: 상위 3개 연도 추출
df_sorted = df_clean.drop_duplicates(subset=['분야 및 연도']).sort_values('총배출량(kt CO2-eq)', ascending=False)
top3_data = df_sorted.head(3).sort_values('분야 및 연도')

# 3단계: 막대 그래프 생성
plt.figure(figsize=(11, 7), dpi=100)
bars = plt.bar(top3_data['분야 및 연도'], top3_data['총배출량(kt CO2-eq)'], 
               color=['#FFD93D', '#FF6B6B', '#4ECDC4'], alpha=0.8, width=0.6)
plt.title('배출량 상위 3개 연도 비교', fontsize=14, fontweight='bold')
plt.xlabel('연도', fontsize=10)
plt.ylabel('총배출량 (kt CO2-eq)', fontsize=10)

# 4단계: X축 연도 설정 및 값 표시
plt.xticks(top3_data['분야 및 연도'], [str(int(year)) + '년' for year in top3_data['분야 및 연도']])
for bar, value in zip(bars, top3_data['총배출량(kt CO2-eq)']):
    plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + value*0.01, 
             str(int(value/1000)) + 'K', ha='center', va='bottom', fontsize=9)

plt.grid(True, alpha=0.3, axis='y')
plt.tight_layout()

# 5단계: 결과 설명 생성
result = "배출량이 가장 높은 상위 3개 연도를 막대 그래프로 비교했습니다. 2022년이 1,234,567 kt CO2-eq로 가장 높고, 2021년 1,201,456 kt CO2-eq, 2020년 1,189,123 kt CO2-eq 순입니다."
table_result = None
```

### 4️⃣ 부문별 분석 질문 (라인 그래프 - 특정 부문)
**패턴**: "에너지", "에너지부문", "에너지 배출량", "산업공정", "농업", "폐기물" 등
**대응**: 해당 부문 컬럼을 사용한 라인 그래프 생성 + 설명

**예시질문 1**: "에너지부문의 배출량 추이를 보여주세요"
```python
# 1단계: NA 값 제거 (필수)
df_clean = df.dropna(subset=['분야 및 연도', '에너지'])

# 2단계: 데이터 중복 제거 및 정렬
df_plot = df_clean.drop_duplicates(subset=['분야 및 연도']).sort_values('분야 및 연도')

# 3단계: 라인 그래프 생성 (에너지 부문 전용)
plt.figure(figsize=(11, 7), dpi=100)
plt.plot(df_plot['분야 및 연도'], df_plot['에너지'], marker='o', linewidth=2, markersize=4, color='#FF9500')
plt.title('에너지 부문 배출량 변화 추세', fontsize=14, fontweight='bold')
plt.xlabel('연도', fontsize=10)
plt.ylabel('에너지 배출량 (kt CO2-eq)', fontsize=10)

# 4단계: X축 연도 설정
unique_years = sorted(df_plot['분야 및 연도'].unique())
plt.xticks(unique_years, [str(int(year)) for year in unique_years])
plt.gca().xaxis.set_major_formatter(FuncFormatter(lambda val, pos: str(int(val))))

plt.grid(True, alpha=0.3)
plt.tight_layout()

# 5단계: 결과 설명 생성
result = "에너지 부문 배출량 변화 추세를 라인 그래프로 생성했습니다. 2017년 456,789 kt CO2-eq에서 2022년 523,456 kt CO2-eq로 총 +66,667 kt CO2-eq (+14.6%) 증가했습니다."
table_result = None
```

**예시질문 2**: "산업공정 부문의 배출량 변화는?"
```python
# 1단계: NA 값 제거 (필수)
df_clean = df.dropna(subset=['분야 및 연도', '산업공정'])

# 2단계: 데이터 중복 제거 및 정렬
df_plot = df_clean.drop_duplicates(subset=['분야 및 연도']).sort_values('분야 및 연도')

# 3단계: 라인 그래프 생성 (산업공정 부문 전용)
plt.figure(figsize=(11, 7), dpi=100)
plt.plot(df_plot['분야 및 연도'], df_plot['산업공정'], marker='s', linewidth=2, markersize=4, color='#34C759')
plt.title('산업공정 부문 배출량 변화 추세', fontsize=14, fontweight='bold')
plt.xlabel('연도', fontsize=10)
plt.ylabel('산업공정 배출량 (kt CO2-eq)', fontsize=10)

# 4단계: X축 연도 설정
unique_years = sorted(df_plot['분야 및 연도'].unique())
plt.xticks(unique_years, [str(int(year)) for year in unique_years])
plt.gca().xaxis.set_major_formatter(FuncFormatter(lambda val, pos: str(int(val))))

plt.grid(True, alpha=0.3)
plt.tight_layout()

# 5단계: 결과 설명 생성
result = "산업공정 부문 배출량 변화 추세를 라인 그래프로 생성했습니다. 2017년 123,456 kt CO2-eq에서 2022년 145,678 kt CO2-eq로 총 +22,222 kt CO2-eq (+18.0%) 증가했습니다."
table_result = None
```

### 5️⃣ 테이블이 필요한 질문
**패턴**: "통계", "요약", "분석", "비교", "상세" 등
**대응**: 테이블 생성 + 설명

**예시질문 1**: "배출량 데이터의 기본 통계를 보여주세요"
```python
# 1단계: NA 값 제거
df_clean = df.dropna(subset=['총배출량(kt CO2-eq)', '순배출량', '에너지'])

# 2단계: 통계 계산
stats_df = df_clean[['총배출량(kt CO2-eq)', '순배출량', '에너지']].describe()

# 3단계: 결과 생성
table_result = stats_df
result = "배출량 데이터의 기본 통계 정보를 표로 제공합니다. 평균, 표준편차, 최솟값, 최댓값 등 주요 통계지표를 확인할 수 있습니다."
```

**예시질문 2**: "연도별 배출량 상세 데이터를 표로 정리해주세요"
```python
# 1단계: NA 값 제거
df_clean = df.dropna(subset=['분야 및 연도', '총배출량(kt CO2-eq)'])

# 2단계: 연도별 데이터 정리
yearly_data = df_clean.drop_duplicates(subset=['분야 및 연도']).sort_values('분야 및 연도')
summary_table = yearly_data[['분야 및 연도', '총배출량(kt CO2-eq)', '순배출량', '에너지']].copy()
summary_table.columns = ['연도', '총배출량', '순배출량', '에너지']

# 3단계: 결과 생성
table_result = summary_table
result = "연도별 배출량 상세 데이터를 표로 정리했습니다. 총배출량, 순배출량, 에너지 부문별 수치를 연도순으로 확인할 수 있습니다."
```

**예시질문 3**: "배출량 증감률을 분석해주세요"
```python
# 1단계: NA 값 제거
df_clean = df.dropna(subset=['분야 및 연도', '총배출량(kt CO2-eq)'])

# 2단계: 연도별 증감률 계산
yearly_data = df_clean.drop_duplicates(subset=['분야 및 연도']).sort_values('분야 및 연도')
yearly_data['전년대비_증감량'] = yearly_data['총배출량(kt CO2-eq)'].diff()
yearly_data['전년대비_증감률(%)'] = yearly_data['총배출량(kt CO2-eq)'].pct_change() * 100

# 3단계: 결과 테이블 생성
analysis_table = yearly_data[['분야 및 연도', '총배출량(kt CO2-eq)', '전년대비_증감량', '전년대비_증감률(%)']].copy()
analysis_table.columns = ['연도', '총배출량', '증감량', '증감률(%)']

# 4단계: 결과 생성
table_result = analysis_table
result = "배출량 증감률 분석 결과를 표로 제공합니다. 각 연도별 총배출량과 전년 대비 증감량, 증감률을 확인할 수 있습니다."
```

## 그래프 유형 선택 지침

### 🔍 질문 분석 및 그래프 유형 결정
**1단계: 질문에서 키워드 확인**
- **라인 그래프 (총배출량)**: "변화", "추이", "트렌드", "최근 N년간", "시간에 따른", "증가", "감소", "총배출량"
- **라인 그래프 (부문별)**: "에너지", "에너지부문", "산업공정", "농업", "폐기물" + "변화", "추이"
- **막대 그래프**: "비교", "차이", "대비", "vs", "A년과 B년", "어느 것이", "중 어느"

**2단계: 데이터 범위 확인**
- **연속적 범위** (예: 2018-2022) → 라인 그래프
- **특정 연도들** (예: 2017, 2021) → 막대 그래프

**3단계: 질문 의도 파악**
- **추세 파악이 목적** → 라인 그래프
- **값 비교가 목적** → 막대 그래프

## 중요한 데이터 처리 지침

### 연도별 분석 시 주의사항
- **기본 컬럼**: '분야 및 연도' (x축), '총배출량(kt CO2-eq)' (y축)
- **최근 N년 필터링**: `df[df['분야 및 연도'] >= (현재연도 - N)]` 형식 사용
- **정확한 컬럼명 사용**: '총배출량(kt CO2-eq)' (괄호와 하이픈 정확히)

### 안전한 데이터 처리 패턴
```python
# 안전한 데이터 처리 순서 (반드시 이 순서를 따르세요)
# 1단계: NA 값 제거 (필수 - 가장 먼저)
df_clean = df.dropna(subset=['분야 및 연도', '총배출량(kt CO2-eq)'])

# 2단계: 데이터 필터링 (필요한 경우)
filtered_data = df_clean[df_clean['분야 및 연도'] >= 2018]

# 3단계: 중복 제거 및 정렬
df_plot = filtered_data.drop_duplicates(subset=['분야 및 연도']).sort_values('분야 및 연도')

# 4단계: 변수 계산 및 정의
start_value = df_plot['총배출량(kt CO2-eq)'].iloc[0]
end_value = df_plot['총배출량(kt CO2-eq)'].iloc[-1]
# ... 기타 필요한 변수들

# 5단계: 그래프 생성 또는 계산 수행

# 6단계: 결과 문자열 생성 (모든 변수가 정의된 후)
result = "결과 설명..."
```

## 📊 코드 작성 핵심 원칙

### ✅ 반드시 지켜야 할 순서
1. **NA 값 제거** → 2. **데이터 필터링** → 3. **변수 정의** → 4. **결과 생성**

### ✅ 변수 사용 규칙
- 모든 변수는 **사용하기 전에 반드시 정의**
- f-string에서 사용하는 모든 변수는 **이미 계산되어 있어야 함**
- 조건문 사용 전 **NA 값 처리 필수**

### ✅ 결과 문자열 패턴
```python
# 올바른 패턴: 변수를 먼저 정의하고 나서 사용
max_year = df_clean.loc[df_clean['총배출량(kt CO2-eq)'].idxmax(), '분야 및 연도']
max_value = df_clean['총배출량(kt CO2-eq)'].max()
result = "가장 높은 연도는 2021년이며, 배출량은 1,234,567 kt CO2-eq입니다."

# 잘못된 패턴: 정의되지 않은 변수 사용 (절대 금지)
result = "가장 높은 연도는 2021년입니다."  # ✅ 구체적 예시 사용
```

## 출력 요구사항
- **단답형**: result에 구체적 수치와 단위가 포함된 답변 문자열, table_result = None
- **라인 그래프**: result에 기간, 시작/끝값, 변화량/비율이 포함된 상세 설명, table_result = None  
- **막대 그래프**: result에 비교 대상별 구체적 수치, 차이값, 증감률이 포함된 상세 설명, table_result = None
- **테이블**: result에 테이블 내용 요약 및 주요 인사이트, table_result에 DataFrame
- 주석은 한글로 작성
- 상세하고 분석적인 설명 제공

## ⚠️ 데이터 정확성 최우선 원칙
- **반드시 전체 통합 데이터(df)를 사용하세요** - 개별 파일이 아닌 concat된 전체 데이터
- 행 수 질문시 `len(df)` 또는 `df.shape[0]`로 **전체 통합 데이터 행 수**를 계산
- 데이터 소스별 정보가 필요한 경우에만 '데이터소스' 컬럼 사용
- 절대로 첫 번째 파일이나 일부 데이터만 참조하지 마세요

## 안전한 코드 작성 지침
- 모든 변수는 사용 전 정의
- 컬럼명 정확성 확인 ('총배출량(kt CO2-eq)' 등)
- **NA/NaN 값 처리 필수**: 조건문 사용 전 반드시 결측값 제거
- 데이터 존재 여부 확인
- try-except로 오류 처리
- print 문 최소 사용

## 🚨 중요: NA/NaN 값 처리 방법

### 필수 데이터 전처리 (모든 코드 시작 부분)
```python
# 1단계: 핵심 컬럼의 NA 값 제거 (반드시 먼저 실행)
df_clean = df.dropna(subset=['분야 및 연도', '총배출량(kt CO2-eq)'])

# 2단계: 정리된 데이터로 작업 진행
# 이후 모든 작업은 df_clean 사용
```

### 안전한 조건문 패턴
```python
# ❌ 위험한 방식 (NA 오류 발생 가능)
filtered_data = df[df['분야 및 연도'] >= 2018]

# ✅ 안전한 방식 (NA 처리 후 조건문)
df_clean = df.dropna(subset=['분야 및 연도'])
filtered_data = df_clean[df_clean['분야 및 연도'] >= 2018]

# 또는 한 줄로
filtered_data = df[(df['분야 및 연도'].notna()) & (df['분야 및 연도'] >= 2018)]
```"""
        
        try:
            response = self.llm.invoke(prompt)
            code = response.content
            
            # 코드 블록 추출
            if "```python" in code:
                code = code.split("```python")[1].split("```")[0]
            elif "```" in code:
                code = code.split("```")[1].split("```")[0]
            
            return code.strip()
            
        except Exception as e:
            print(f"❌ 코드 생성 실패: {e}")
            return None
    
    def _execute_code(self, code: str) -> Tuple[str, bool, Optional[pd.DataFrame], Optional[object]]:
        """안전하게 코드 실행"""
        if not code:
            return "코드를 생성할 수 없습니다.", False, None, None
        
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
                    return f"보안상 위험한 코드가 감지되었습니다: {pattern}", False, None, None
            
            # 안전한 실행 환경 구성
            safe_builtins = {
                'len': len, 'str': str, 'int': int, 'float': float,
                'list': list, 'dict': dict, 'tuple': tuple,
                'range': range, 'enumerate': enumerate,
                'sum': sum, 'min': min, 'max': max,
                'abs': abs, 'round': round,
                'print': print,  # print 함수 추가
                'type': type, 'isinstance': isinstance,
                'sorted': sorted, 'reversed': reversed,
                'zip': zip, 'any': any, 'all': all,
                'bool': bool, 'set': set,
                '__import__': __import__  # matplotlib 등에서 필요
            }
            
            namespace = {
                '__builtins__': safe_builtins,
                'df': self.df,
                'pd': pd,
                'plt': plt,
                'sns': sns,
                'FuncFormatter': FuncFormatter,
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
                return f"변수 정의 오류: {str(ne)}. 모든 변수를 사용하기 전에 정의해주세요.", False, None, None
            except Exception as exec_error:
                sys.stdout = old_stdout
                plt.close('all')
                return f"코드 실행 중 오류: {str(exec_error)}", False, None, None
            
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
                        print(f"✅ 그래프 생성됨: figure 객체 추출 완료")
                    else:
                        figure_obj = None
                        has_plot = False
                except Exception as e:
                    print(f"⚠️ 그래프 객체 추출 실패: {e}")
                    figure_obj = None
                    has_plot = False
            
            # 디버깅 정보
            if has_plot:
                print(f"✅ 그래프 생성됨: {figs_before} -> {figs_after}")
            if table_result is not None:
                print(f"✅ 테이블 생성됨: {table_result.shape}")
            
            return str(result), has_plot, table_result, figure_obj
            
        except Exception as e:
            sys.stdout = old_stdout
            plt.close('all')  # 오류 시에도 그래프 정리
            return f"코드 실행 오류: {str(e)}", False, None, None
    
    def ask(self, question: str) -> Tuple[str, Optional[str], Optional[pd.DataFrame], Optional[object]]:
        """
        질문에 대한 답변 생성
        
        Args:
            question: 사용자 질문
            
        Returns:
            Tuple[str, Optional[str], Optional[pd.DataFrame], Optional[object]]: (답변, 시각화_데이터, 테이블_데이터, figure_객체)
        """
        if not self.llm:
            return "❌ LLM이 초기화되지 않았습니다.", None, None, None
        
        if self.df is None or self.df.empty:
            return "❌ 데이터가 로드되지 않았습니다.", None, None, None
        
        try:
            # 1. 코드 생성
            code = self._generate_code(question)
            if not code:
                return "❌ 분석 코드를 생성할 수 없습니다.", None, None, None
            
            # 2. 코드 실행
            result, has_plot, table_result, figure_obj = self._execute_code(code)
            
            # 3. 결과가 없으면 기본 답변 생성
            if not result or result.strip() == "":
                if has_plot:
                    result = "요청하신 데이터를 분석하여 그래프를 생성했습니다."
                elif table_result is not None:
                    result = "요청하신 통계 정보를 테이블로 생성했습니다."
                else:
                    result = "데이터 분석을 완료했습니다."
            
            # 4. 그래프 생성 여부, 테이블 데이터, figure 객체를 반환
            return result, "plot_generated" if has_plot else None, table_result, figure_obj
            
        except Exception as e:
            return f"❌ 오류가 발생했습니다: {str(e)}", None, None, None
    
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


# 사용 예시
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
        
        print("🤔 분석 중...")
        answer, _, _, _ = agent.ask(question)
        print(f"🤖 답변: {answer}") 