#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
K-ETS Dashboard 보안 및 인증 관리
"""

from datetime import datetime, timedelta
from typing import Optional, Union
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

# 비밀번호 해싱 컨텍스트
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT 토큰 스키마
security = HTTPBearer()

# JWT 토큰 설정
ALGORITHM = "HS256"

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """비밀번호 검증"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """비밀번호 해싱"""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """액세스 토큰 생성"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    
    return encoded_jwt

def verify_token(token: str) -> Optional[dict]:
    """토큰 검증 및 디코딩"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        
        if username is None:
            return None
            
        return payload
    except JWTError:
        return None

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """현재 인증된 사용자 정보 가져오기"""
    token = credentials.credentials
    
    payload = verify_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 인증 정보",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    username: str = payload.get("sub")
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 인증 정보",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return payload

def require_auth(func):
    """인증이 필요한 엔드포인트 데코레이터"""
    async def wrapper(*args, **kwargs):
        # 여기서 인증 로직 구현
        # 실제로는 get_current_user를 사용
        return await func(*args, **kwargs)
    return wrapper

# API 키 인증
def verify_api_key(api_key: str) -> bool:
    """API 키 검증"""
    valid_keys = [
        settings.KOREA_ENERGY_API_KEY,
        settings.ENVIRONMENT_API_KEY
    ]
    return api_key in valid_keys and api_key != ""

async def get_api_key_user(api_key: str) -> Optional[dict]:
    """API 키로 사용자 정보 가져오기"""
    if verify_api_key(api_key):
        return {
            "type": "api_key",
            "permissions": ["read", "write"]
        }
    return None

# 권한 검증
def check_permission(user: dict, required_permission: str) -> bool:
    """사용자 권한 검증"""
    user_permissions = user.get("permissions", [])
    return required_permission in user_permissions

def require_permission(permission: str):
    """특정 권한이 필요한 데코레이터"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # 권한 검증 로직 구현
            return await func(*args, **kwargs)
        return wrapper
    return decorator

# 보안 헤더 설정
def get_security_headers() -> dict:
    """보안 헤더 반환"""
    return {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains"
    }

# 로그인 함수 (실제 구현에서는 데이터베이스와 연동)
async def authenticate_user(username: str, password: str) -> Optional[dict]:
    """사용자 인증"""
    # 실제 구현에서는 데이터베이스에서 사용자 정보 조회
    # 여기서는 예시용 하드코딩된 사용자
    if username == "admin" and password == "admin123":
        return {
            "username": username,
            "full_name": "관리자",
            "email": "admin@kets.kr",
            "permissions": ["read", "write", "admin"]
        }
    return None

# 보안 이벤트 로깅
def log_security_event(event_type: str, user: str, details: str, ip_address: str = None):
    """보안 이벤트 로깅"""
    logger.warning(
        f"보안 이벤트: {event_type} | 사용자: {user} | 상세: {details} | IP: {ip_address}"
    )
