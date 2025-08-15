#!/usr/bin/env python3
"""
데이터 구조 확인 서비스
FastAPI에서 사용할 수 있도록 수정된 버전
"""

import pandas as pd
import os
from pathlib import Path
from typing import Dict, List, Any, Optional

class DataStructureChecker:
    """데이터 구조 분석 서비스 클래스"""
    
    def __init__(self, data_folder: str = "data"):
        """초기화"""
        self.data_folder = Path(data_folder)
        self.csv_files = [
            "환경부 온실가스종합정보센터_국가 온실가스 인벤토리 배출량_20250103.csv",
            "배출권_거래데이터.csv", 
            "01. 3차_사전할당_20250613090824.csv",
            "한국에너지공단_산업부문 에너지사용 및 온실가스배출량 통계_20231231.csv"
        ]
    
    def analyze_file_structure(self, filename: str) -> Optional[Dict[str, Any]]:
        """단일 파일의 구조 분석"""
        filepath = self.data_folder / filename
        if not filepath.exists():
            return None
            
        # 다양한 인코딩으로 시도
        for encoding in ['cp949', 'euc-kr', 'utf-8', 'utf-8-sig']:
            try:
                df = pd.read_csv(filepath, encoding=encoding, low_memory=False)
                
                # 연도 관련 컬럼 찾기
                year_cols = []
                for col in df.columns:
                    col_lower = str(col).lower()
                    if any(pattern in col_lower for pattern in ['연도', 'year', '년도', '년']):
                        year_cols.append(col)
                
                # 배출량 관련 컬럼 찾기
                emission_cols = []
                for col in df.columns:
                    col_lower = str(col).lower()
                    if any(pattern in col_lower for pattern in ['배출량', '배출', 'emission', 'co2']):
                        emission_cols.append(col)
                
                # 결과 구성
                result = {
                    "filename": filename,
                    "encoding": encoding,
                    "shape": df.shape,
                    "columns": df.columns.tolist(),
                    "main_columns": df.columns[:10].tolist(),
                    "year_columns": year_cols,
                    "emission_columns": emission_cols[:5],
                    "sample_data": df.head(3).to_dict('records'),
                    "data_types": df.dtypes.to_dict()
                }
                
                # 연도 컬럼 샘플 데이터
                if year_cols:
                    year_samples = {}
                    for col in year_cols[:3]:
                        year_samples[col] = df[col].dropna().head(5).tolist()
                    result["year_samples"] = year_samples
                
                return result
                
            except UnicodeDecodeError:
                continue
                
        return None
    
    def check_all_data_structure(self) -> Dict[str, Any]:
        """모든 데이터 파일의 구조 분석"""
        results = {}
        
        for filename in self.csv_files:
            file_result = self.analyze_file_structure(filename)
            if file_result:
                results[filename] = file_result
            else:
                results[filename] = {"error": "로드 실패"}
        
        return {
            "data_folder": str(self.data_folder),
            "total_files": len(self.csv_files),
            "analyzed_files": len([r for r in results.values() if "error" not in r]),
            "results": results
        }
    
    def get_summary(self) -> Dict[str, Any]:
        """데이터 구조 요약 정보"""
        analysis = self.check_all_data_structure()
        
        summary = {
            "total_files": analysis["total_files"],
            "successfully_analyzed": analysis["analyzed_files"],
            "failed_files": analysis["total_files"] - analysis["analyzed_files"],
            "available_columns": {},
            "common_patterns": {
                "year_columns": [],
                "emission_columns": []
            }
        }
        
        # 공통 컬럼 패턴 추출
        all_year_cols = set()
        all_emission_cols = set()
        
        for filename, result in analysis["results"].items():
            if "error" not in result:
                summary["available_columns"][filename] = len(result["columns"])
                all_year_cols.update(result["year_columns"])
                all_emission_cols.update(result["emission_columns"])
        
        summary["common_patterns"]["year_columns"] = list(all_year_cols)
        summary["common_patterns"]["emission_columns"] = list(all_emission_cols)
        
        return summary

# 하위 호환성을 위한 함수
def check_data_structure():
    """기존 함수와의 호환성 유지"""
    checker = DataStructureChecker()
    analysis = checker.check_all_data_structure()
    
    print("📊 데이터 구조 분석 시작")
    print("=" * 50)
    
    for filename, result in analysis["results"].items():
        if "error" in result:
            print(f"\n❌ 로드 실패: {filename}")
            continue
            
        print(f"\n📁 파일: {filename}")
        print("-" * 40)
        print(f"✅ 인코딩: {result['encoding']}")
        print(f"   크기: {result['shape']}")
        print(f"   컬럼 수: {len(result['columns'])}")
        
        print("   주요 컬럼:")
        for i, col in enumerate(result['main_columns']):
            print(f"     {i+1}. {col}")
        
        if result['year_columns']:
            print(f"   연도 관련 컬럼: {result['year_columns']}")
            
        if result['emission_columns']:
            print(f"   배출량 관련 컬럼: {result['emission_columns']}")
    
    return analysis

if __name__ == "__main__":
    check_data_structure() 