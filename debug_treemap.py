import pandas as pd
import numpy as np

def analyze_treemap_data():
    """트리맵 데이터 분석"""
    files = [
        ('data/01. 3차_사전할당_20250613090824.csv', 'cp949'),
        ('data/02. 추가할당량_20250613090916.csv', 'cp949'),
        ('data/03. 상쇄배출권 발행량_20250613090944.csv', 'cp949')
    ]
    
    for i, (file, encoding) in enumerate(files):
        print(f"\n=== {file} 분석 ===")
        try:
            df = pd.read_csv(file, encoding=encoding)
            print(f"전체 행 수: {len(df)}")
            print(f"컬럼: {list(df.columns)}")
            
            # 연도별 컬럼 찾기
            year_cols = [c for c in df.columns if '202' in c or '발행수량' in c]
            print(f"연도별 컬럼: {year_cols}")
            
            for col in year_cols:
                if col in df.columns:
                    # 데이터 타입 확인
                    print(f"\n{col} 컬럼 분석:")
                    print(f"  데이터 타입: {df[col].dtype}")
                    print(f"  NaN 개수: {df[col].isna().sum()}")
                    print(f"  0 개수: {(df[col] == 0).sum()}")
                    print(f"  음수 개수: {(df[col] < 0).sum()}")
                    print(f"  양수 개수: {(df[col] > 0).sum()}")
                    
                    # 실제 값들 확인
                    non_zero = df[df[col] > 0][col]
                    if len(non_zero) > 0:
                        print(f"  양수 값 샘플: {non_zero.head().tolist()}")
                        print(f"  최대값: {non_zero.max()}")
                        print(f"  최소값: {non_zero.min()}")
                    else:
                        print(f"  양수 값 없음")
                    
                    # 업종별 통계
                    if '업종' in df.columns:
                        print(f"\n  업종별 {col} 통계:")
                        sector_stats = df.groupby('업종')[col].agg(['count', 'sum', 'mean'])
                        print(sector_stats.head())
            
            # 샘플 데이터
            print(f"\n샘플 데이터 (처음 3행):")
            print(df.head(3))
            
        except Exception as e:
            print(f"파일 읽기 오류: {e}")

if __name__ == "__main__":
    analyze_treemap_data() 