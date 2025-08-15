"""
데이터 검증 서비스
FastAPI에서 사용할 수 있도록 수정된 버전
"""

import pandas as pd
import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Union

class DataValidator:
    """데이터 검증 서비스 클래스"""
    
    def __init__(self, data_folder: str = "data"):
        """초기화"""
        self.data_folder = Path(data_folder)
        self.csv_files = [
            '환경부 온실가스종합정보센터_국가 온실가스 인벤토리 배출량_20250103.csv',
            'CLM_온실가스_DD_20250612201816.csv',
            '배출권_거래데이터.csv',
            '01. 3차_사전할당_20250613090824.csv',
            '02. 추가할당량_20250613090916.csv',
            '03. 상쇄배출권 발행량_20250613090944.csv',
            '배출권총수량_20250613090514.csv'
        ]
        self.excel_files = [
            '기업_규모_지역별_온실가스_배출량_20250615183643.xlsx',
            'HOME_발전·판매_발전량_전원별.xlsx'
        ]
    
    def validate_excel_file(self, filename: str) -> Dict[str, Any]:
        """Excel 파일 검증"""
        filepath = self.data_folder / filename
        result = {
            "filename": filename,
            "exists": filepath.exists(),
            "sheets": {},
            "error": None
        }
        
        if not filepath.exists():
            result["error"] = "파일이 존재하지 않습니다"
            return result
            
        try:
            df_dict = pd.read_excel(filepath, sheet_name=None)
            
            for sheet_name, df in df_dict.items():
                result["sheets"][sheet_name] = {
                    "columns": list(df.columns),
                    "rows": len(df),
                    "shape": df.shape,
                    "data_types": df.dtypes.to_dict(),
                    "sample_data": df.head(3).to_dict('records')
                }
                
        except Exception as e:
            result["error"] = f"Excel 파일 읽기 오류: {str(e)}"
            
        return result
    
    def validate_csv_file(self, filename: str) -> Dict[str, Any]:
        """CSV 파일 검증"""
        filepath = self.data_folder / filename
        result = {
            "filename": filename,
            "exists": filepath.exists(),
            "encoding": None,
            "shape": None,
            "columns": [],
            "sample_data": [],
            "error": None
        }
        
        if not filepath.exists():
            result["error"] = "파일이 존재하지 않습니다"
            return result
        
        # 여러 인코딩 시도
        for encoding in ['cp949', 'euc-kr', 'utf-8', 'utf-8-sig']:
            try:
                df = pd.read_csv(filepath, encoding=encoding, nrows=5)
                result.update({
                    "encoding": encoding,
                    "shape": (len(pd.read_csv(filepath, encoding=encoding)), len(df.columns)),
                    "columns": list(df.columns),
                    "sample_data": df.head(3).to_dict('records'),
                    "data_types": df.dtypes.to_dict()
                })
                break
            except UnicodeDecodeError:
                continue
            except Exception as e:
                result["error"] = f"파일 읽기 오류: {str(e)}"
                break
        else:
            if not result["error"]:
                result["error"] = "지원되는 인코딩을 찾을 수 없습니다"
                
        return result
    
    def validate_all_files(self) -> Dict[str, Any]:
        """모든 데이터 파일 검증"""
        results = {
            "csv_files": {},
            "excel_files": {},
            "summary": {
                "total_csv": len(self.csv_files),
                "total_excel": len(self.excel_files),
                "valid_csv": 0,
                "valid_excel": 0,
                "errors": []
            }
        }
        
        # CSV 파일 검증
        for filename in self.csv_files:
            result = self.validate_csv_file(filename)
            results["csv_files"][filename] = result
            
            if not result["error"] and result["exists"]:
                results["summary"]["valid_csv"] += 1
            elif result["error"]:
                results["summary"]["errors"].append(f"CSV {filename}: {result['error']}")
        
        # Excel 파일 검증
        for filename in self.excel_files:
            result = self.validate_excel_file(filename)
            results["excel_files"][filename] = result
            
            if not result["error"] and result["exists"]:
                results["summary"]["valid_excel"] += 1
            elif result["error"]:
                results["summary"]["errors"].append(f"Excel {filename}: {result['error']}")
        
        return results
    
    def get_file_info(self, filename: str) -> Optional[Dict[str, Any]]:
        """특정 파일 정보 조회"""
        if filename in self.csv_files:
            return self.validate_csv_file(filename)
        elif filename in self.excel_files:
            return self.validate_excel_file(filename)
        else:
            return {"error": "지원되지 않는 파일입니다"}
    
    def check_data_quality(self, filename: str) -> Dict[str, Any]:
        """데이터 품질 검사"""
        filepath = self.data_folder / filename
        if not filepath.exists():
            return {"error": "파일이 존재하지 않습니다"}
        
        try:
            # 파일 타입에 따라 처리
            if filename.endswith('.xlsx'):
                df_dict = pd.read_excel(filepath, sheet_name=None)
                quality_results = {}
                
                for sheet_name, df in df_dict.items():
                    quality_results[sheet_name] = self._analyze_dataframe_quality(df)
                    
                return {"sheets": quality_results}
            else:
                # CSV 파일 처리
                for encoding in ['cp949', 'euc-kr', 'utf-8', 'utf-8-sig']:
                    try:
                        df = pd.read_csv(filepath, encoding=encoding)
                        return self._analyze_dataframe_quality(df)
                    except UnicodeDecodeError:
                        continue
                
                return {"error": "파일을 읽을 수 없습니다"}
                
        except Exception as e:
            return {"error": f"데이터 품질 검사 실패: {str(e)}"}
    
    def _analyze_dataframe_quality(self, df: pd.DataFrame) -> Dict[str, Any]:
        """DataFrame 품질 분석"""
        return {
            "total_rows": len(df),
            "total_columns": len(df.columns),
            "missing_values": df.isnull().sum().to_dict(),
            "missing_percentage": (df.isnull().sum() / len(df) * 100).to_dict(),
            "duplicate_rows": df.duplicated().sum(),
            "data_types": df.dtypes.to_dict(),
            "numeric_columns": df.select_dtypes(include=['number']).columns.tolist(),
            "categorical_columns": df.select_dtypes(include=['object']).columns.tolist(),
            "memory_usage": df.memory_usage(deep=True).sum()
        }

# 하위 호환성을 위한 함수들
def check_excel_file():
    """Excel 파일 확인 (하위 호환성)"""
    validator = DataValidator()
    excel_files = validator.excel_files
    
    for filename in excel_files:
        result = validator.validate_excel_file(filename)
        
        print(f"=== Excel 파일: {filename} ===")
        if result["error"]:
            print(f"오류: {result['error']}")
            continue
            
        for sheet_name, sheet_info in result["sheets"].items():
            print(f"시트: {sheet_name}")
            print(f"컬럼: {sheet_info['columns']}")
            print(f"행 수: {sheet_info['rows']}")
            print("---")

def check_csv_files():
    """CSV 파일들 확인 (하위 호환성)"""
    validator = DataValidator()
    csv_files = validator.csv_files
    
    for filename in csv_files:
        result = validator.validate_csv_file(filename)
        
        print(f"\n=== {filename} ===")
        if result["error"]:
            print(f"오류: {result['error']}")
            continue
            
        print(f"인코딩: {result['encoding']}")
        print(f"컬럼: {result['columns']}")
        print(f"데이터 샘플:")
        for i, row in enumerate(result['sample_data']):
            print(f"  행 {i+1}: {row}")

if __name__ == "__main__":
    print("데이터 파일 구조 확인")
    print("=" * 50)
    
    check_excel_file()
    check_csv_files() 