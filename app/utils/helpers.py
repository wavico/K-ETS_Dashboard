#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
K-ETS Dashboard 헬퍼 유틸리티
"""

import os
import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
import pandas as pd

def generate_file_id(filename: str) -> str:
    """파일 ID 생성"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    name_hash = hashlib.md5(filename.encode()).hexdigest()[:8]
    return f"{timestamp}_{name_hash}"

def validate_file_extension(filename: str, allowed_extensions: List[str]) -> bool:
    """파일 확장자 검증"""
    file_ext = os.path.splitext(filename)[1].lower()
    return file_ext in allowed_extensions

def get_file_size_mb(file_path: str) -> float:
    """파일 크기 (MB) 반환"""
    if os.path.exists(file_path):
        size_bytes = os.path.getsize(file_path)
        return size_bytes / (1024 * 1024)
    return 0.0

def create_directory_if_not_exists(directory_path: str) -> bool:
    """디렉토리가 없으면 생성"""
    try:
        if not os.path.exists(directory_path):
            os.makedirs(directory_path)
            return True
        return True
    except Exception:
        return False

def format_file_size(size_bytes: int) -> str:
    """파일 크기 포맷팅"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"

def parse_date_range(date_range: str) -> tuple:
    """날짜 범위 파싱"""
    today = datetime.now()
    
    if date_range == "7d":
        start_date = today - timedelta(days=7)
        end_date = today
    elif date_range == "30d":
        start_date = today - timedelta(days=30)
        end_date = today
    elif date_range == "90d":
        start_date = today - timedelta(days=90)
        end_date = today
    elif date_range == "1y":
        start_date = today - timedelta(days=365)
        end_date = today
    else:
        start_date = today - timedelta(days=30)
        end_date = today
    
    return start_date, end_date

def safe_json_loads(json_string: str, default: Any = None) -> Any:
    """안전한 JSON 파싱"""
    try:
        return json.loads(json_string)
    except (json.JSONDecodeError, TypeError):
        return default

def safe_json_dumps(data: Any, default: str = "{}") -> str:
    """안전한 JSON 직렬화"""
    try:
        return json.dumps(data, ensure_ascii=False, default=str)
    except (TypeError, ValueError):
        return default

def extract_numeric_value(value: Any) -> Optional[float]:
    """숫자 값 추출"""
    if value is None:
        return None
    
    try:
        if isinstance(value, (int, float)):
            return float(value)
        elif isinstance(value, str):
            # 쉼표 제거 후 숫자 변환
            cleaned = value.replace(',', '').replace(' ', '')
            return float(cleaned)
        else:
            return float(value)
    except (ValueError, TypeError):
        return None

def calculate_percentage_change(current: float, previous: float) -> float:
    """백분율 변화 계산"""
    if previous == 0:
        return 0.0
    return ((current - previous) / previous) * 100

def format_percentage(value: float, decimal_places: int = 2) -> str:
    """백분율 포맷팅"""
    return f"{value:.{decimal_places}f}%"

def validate_email(email: str) -> bool:
    """이메일 주소 검증"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def sanitize_filename(filename: str) -> str:
    """파일명 정리 (안전하지 않은 문자 제거)"""
    import re
    # 안전하지 않은 문자를 언더스코어로 대체
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # 공백을 언더스코어로 대체
    sanitized = re.sub(r'\s+', '_', sanitized)
    return sanitized

def get_dataframe_info(df: pd.DataFrame) -> Dict[str, Any]:
    """데이터프레임 정보 반환"""
    return {
        "shape": df.shape,
        "columns": df.columns.tolist(),
        "dtypes": df.dtypes.to_dict(),
        "memory_usage": df.memory_usage(deep=True).sum(),
        "null_counts": df.isnull().sum().to_dict(),
        "sample_data": df.head(3).to_dict('records')
    }

def chunk_list(lst: List[Any], chunk_size: int) -> List[List[Any]]:
    """리스트를 청크로 분할"""
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]

def flatten_list(nested_list: List[Any]) -> List[Any]:
    """중첩된 리스트를 평면화"""
    flattened = []
    for item in nested_list:
        if isinstance(item, list):
            flattened.extend(flatten_list(item))
        else:
            flattened.append(item)
    return flattened

def get_unique_values(data: List[Any]) -> List[Any]:
    """고유 값 목록 반환 (순서 유지)"""
    seen = set()
    unique = []
    for item in data:
        if item not in seen:
            seen.add(item)
            unique.append(item)
    return unique

def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """안전한 나눗셈 (0으로 나누기 방지)"""
    try:
        if denominator == 0:
            return default
        return numerator / denominator
    except (TypeError, ValueError):
        return default
