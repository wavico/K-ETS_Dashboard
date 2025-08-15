#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
K-ETS Dashboard API 의존성 관리
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Dict, Any
import logging

from app.core.security import verify_token, verify_api_key
from app.core.database import get_db
from app.utils.logger import get_logger

logger = get_logger(__name__)

# HTTP Bearer 인증 스키마
security = HTTPBearer(auto_error=False)

async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[Dict[str, Any]]:
    """선택적 사용자 인증 (인증이 실패해도 None 반환)"""
    if not credentials:
        return None
    
    try:
        payload = verify_token(credentials.credentials)
        return payload
    except Exception as e:
        logger.warning(f"토큰 검증 실패: {e}")
        return None

async def get_current_user_required(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Dict[str, Any]:
    """필수 사용자 인증 (인증 실패 시 401 오류)"""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="인증이 필요합니다",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        payload = verify_token(credentials.credentials)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="유효하지 않은 인증 정보",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return payload
    except Exception as e:
        logger.error(f"토큰 검증 오류: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="인증 정보 검증 실패",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_api_key_user(
    api_key: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """API 키 기반 사용자 인증"""
    if not api_key:
        return None
    
    try:
        user = await verify_api_key(api_key)
        return user
    except Exception as e:
        logger.warning(f"API 키 검증 실패: {e}")
        return None

def require_permission(permission: str):
    """특정 권한이 필요한 의존성 데코레이터"""
    async def permission_dependency(
        current_user: Dict[str, Any] = Depends(get_current_user_required)
    ) -> Dict[str, Any]:
        user_permissions = current_user.get("permissions", [])
        
        if permission not in user_permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"'{permission}' 권한이 필요합니다"
            )
        
        return current_user
    
    return permission_dependency

def require_admin():
    """관리자 권한이 필요한 의존성"""
    return require_permission("admin")

def require_write_permission():
    """쓰기 권한이 필요한 의존성"""
    return require_permission("write")

def require_read_permission():
    """읽기 권한이 필요한 의존성"""
    return require_permission("read")

# 데이터베이스 의존성
async def get_database():
    """데이터베이스 세션 의존성"""
    async for db in get_db():
        yield db

# 캐시 의존성 (Redis)
async def get_cache():
    """캐시 연결 의존성"""
    # 실제 구현에서는 Redis 연결 반환
    # 여기서는 더미 캐시 객체 반환
    class DummyCache:
        async def get(self, key: str):
            return None
        
        async def set(self, key: str, value: Any, ttl: int = 3600):
            pass
        
        async def delete(self, key: str):
            pass
    
    return DummyCache()

# 외부 API 의존성
async def get_external_api_client():
    """외부 API 클라이언트 의존성"""
    # 실제 구현에서는 외부 API 클라이언트 반환
    class ExternalAPIClient:
        def __init__(self):
            self.base_url = "https://api.example.com"
        
        async def get(self, endpoint: str):
            # 더미 응답
            return {"status": "success", "data": "dummy_data"}
    
    return ExternalAPIClient()

# 로깅 의존성
def get_request_logger():
    """요청별 로거 의존성"""
    return logger

# 메트릭 수집 의존성
async def collect_metrics(
    endpoint: str,
    method: str,
    user_id: Optional[str] = None,
    response_time: Optional[float] = None
):
    """API 메트릭 수집"""
    try:
        # 실제 구현에서는 메트릭 수집 시스템에 데이터 전송
        logger.info(f"메트릭: {method} {endpoint} - 사용자: {user_id}, 응답시간: {response_time}ms")
    except Exception as e:
        logger.error(f"메트릭 수집 실패: {e}")

# 비율 제한 의존성
async def check_rate_limit(
    user_id: Optional[str] = None,
    endpoint: str = "",
    limit: int = 100
):
    """API 비율 제한 확인"""
    # 실제 구현에서는 Redis나 다른 저장소에서 비율 제한 확인
    # 여기서는 항상 허용
    return True

# 요청 검증 의존성
def validate_request_size(max_size: int = 1024 * 1024):  # 1MB 기본값
    """요청 크기 검증 의존성"""
    async def size_validator(request):
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > max_size:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"요청 크기가 너무 큽니다. 최대 {max_size} bytes까지 허용됩니다."
            )
        return request
    
    return size_validator
