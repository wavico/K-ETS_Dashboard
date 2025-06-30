#!/usr/bin/env python3
"""
데이터 구조 확인 스크립트
실제 CSV 데이터의 구조를 분석합니다.
"""

import pandas as pd
import os
from pathlib import Path

def check_data_structure():
    """데이터 구조 분석"""
    print("📊 데이터 구조 분석 시작")
    print("=" * 50)
    
    data_folder = Path("data")
    csv_files = [
        "환경부 온실가스종합정보센터_국가 온실가스 인벤토리 배출량_20250103.csv",
        "배출권_거래데이터.csv",
        "01. 3차_사전할당_20250613090824.csv",
        "한국에너지공단_산업부문 에너지사용 및 온실가스배출량 통계_20231231.csv"
    ]
    
    for filename in csv_files:
        filepath = data_folder / filename
        if filepath.exists():
            print(f"\n📁 파일: {filename}")
            print("-" * 40)
            
            # 다양한 인코딩으로 시도
            for encoding in ['cp949', 'euc-kr', 'utf-8', 'utf-8-sig']:
                try:
                    df = pd.read_csv(filepath, encoding=encoding, low_memory=False)
                    print(f"✅ 인코딩: {encoding}")
                    print(f"   크기: {df.shape}")
                    print(f"   컬럼 수: {len(df.columns)}")
                    
                    # 처음 5개 컬럼명 출력
                    print("   주요 컬럼:")
                    for i, col in enumerate(df.columns[:10]):
                        print(f"     {i+1}. {col}")
                    
                    # 연도 관련 컬럼 찾기
                    year_cols = []
                    for col in df.columns:
                        col_lower = str(col).lower()
                        if any(pattern in col_lower for pattern in ['연도', 'year', '년도', '년']):
                            year_cols.append(col)
                    
                    if year_cols:
                        print(f"   연도 관련 컬럼: {year_cols}")
                        for col in year_cols[:3]:  # 처음 3개만 샘플 출력
                            sample_vals = df[col].dropna().head(5).tolist()
                            print(f"     {col}: {sample_vals}")
                    
                    # 배출량 관련 컬럼 찾기
                    emission_cols = []
                    for col in df.columns:
                        col_lower = str(col).lower()
                        if any(pattern in col_lower for pattern in ['배출량', '배출', 'emission', 'co2']):
                            emission_cols.append(col)
                    
                    if emission_cols:
                        print(f"   배출량 관련 컬럼: {emission_cols[:5]}")  # 처음 5개만
                    
                    # 데이터 샘플 (처음 3행)
                    print("   데이터 샘플:")
                    print(df.head(3).to_string()[:500] + "..." if len(df.head(3).to_string()) > 500 else df.head(3).to_string())
                    
                    break
                except UnicodeDecodeError:
                    continue
            else:
                print(f"❌ 로드 실패: {filename}")

if __name__ == "__main__":
    check_data_structure() 