import pandas as pd
import os

def check_excel_file():
    """Excel 파일 확인"""
    try:
        df = pd.read_excel('data/기업_규모_지역별_온실가스_배출량_20250615183643.xlsx', sheet_name=None)
        print("=== Excel 파일 시트 목록 ===")
        for sheet_name in df.keys():
            print(f"시트: {sheet_name}")
            print(f"컬럼: {list(df[sheet_name].columns)}")
            print(f"행 수: {len(df[sheet_name])}")
            print("---")
    except Exception as e:
        print(f"Excel 파일 읽기 오류: {e}")

def check_csv_files():
    """CSV 파일들 확인"""
    csv_files = [
        'data/환경부 온실가스종합정보센터_국가 온실가스 인벤토리 배출량_20250103.csv',
        'data/CLM_온실가스_DD_20250612201816.csv',
        'data/배출권_거래데이터.csv',
        'data/01. 3차_사전할당_20250613090824.csv',
        'data/02. 추가할당량_20250613090916.csv',
        'data/03. 상쇄배출권 발행량_20250613090944.csv',
        'data/배출권총수량_20250613090514.csv'
    ]
    
    for file_path in csv_files:
        if os.path.exists(file_path):
            print(f"\n=== {file_path} ===")
            try:
                # 여러 인코딩 시도
                for encoding in ['cp949', 'euc-kr', 'utf-8']:
                    try:
                        df = pd.read_csv(file_path, encoding=encoding, nrows=5)
                        print(f"인코딩: {encoding}")
                        print(f"컬럼: {list(df.columns)}")
                        print(f"데이터 샘플:")
                        print(df.head())
                        break
                    except UnicodeDecodeError:
                        continue
            except Exception as e:
                print(f"파일 읽기 오류: {e}")
        else:
            print(f"\n=== {file_path} (파일 없음) ===")

if __name__ == "__main__":
    print("데이터 파일 구조 확인")
    print("=" * 50)
    
    check_excel_file()
    check_csv_files() 