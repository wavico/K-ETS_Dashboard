#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
K-ETS Dashboard 설정 관리
"""

import os
from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    """애플리케이션 설정"""
    
    # 기본 설정
    APP_NAME: str = "K-ETS Dashboard"
    VERSION: str = "1.0.0"
    DEBUG: bool = Field(default=False, env="DEBUG")
    
    # 서버 설정
    HOST: str = Field(default="0.0.0.0", env="HOST")
    PORT: int = Field(default=8000, env="PORT")
    
    # CORS 설정
    ALLOWED_HOSTS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000", "http://127.0.0.1:3000"],
        env="ALLOWED_HOSTS"
    )
    
    # 데이터베이스 설정
    DATABASE_URL: str = Field(
        default="sqlite:///./kets_dashboard.db",
        env="DATABASE_URL"
    )
    
    # 보안 설정
    SECRET_KEY: str = Field(
        default="your-secret-key-change-in-production",
        env="SECRET_KEY"
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    
    # 데이터 폴더 설정
    DATA_FOLDER: str = Field(default="data", env="DATA_FOLDER")
    
    # AI 모델 설정
    OPENAI_API_KEY: str = Field(default="", env="OPENAI_API_KEY")
    OPENAI_MODEL: str = Field(default="gpt-3.5-turbo", env="OPENAI_MODEL")
    UPSTAGE_API_KEY: str = Field(default="", env="UPSTAGE_API_KEY")

    # vLLM 설정
    USE_VLLM: bool = Field(default=True, env="USE_VLLM")
    VLLM_BASE_URL: str = Field(default="http://localhost:8000/v1", env="VLLM_BASE_URL")
    VLLM_MODEL_NAME: str = Field(default="gpt-4-turbo", env="VLLM_MODEL_NAME")  # vLLM에서 served-model-name
    VLLM_API_KEY: str = Field(default="EMPTY", env="VLLM_API_KEY")  # vLLM은 API 키 불필요
    
    # 로깅 설정
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    LOG_FILE: str = Field(default="logs/kets_dashboard.log", env="LOG_FILE")
    
    # 외부 API 설정
    KOREA_ENERGY_API_KEY: str = Field(default="", env="KOREA_ENERGY_API_KEY")
    ENVIRONMENT_API_KEY: str = Field(default="", env="ENVIRONMENT_API_KEY")
    
    # 캐시 설정
    REDIS_URL: str = Field(default="redis://localhost:6379", env="REDIS_URL")
    CACHE_TTL: int = Field(default=3600, env="CACHE_TTL")  # 1시간
    
    # 파일 업로드 설정
    MAX_FILE_SIZE: int = Field(default=100 * 1024 * 1024, env="MAX_FILE_SIZE")  # 100MB
    UPLOAD_FOLDER: str = Field(default="uploads", env="UPLOAD_FOLDER")
    
    # 예측 모델 설정
    PROPHET_CHANGEPOINT_PRIOR_SCALE: float = Field(default=0.05, env="PROPHET_CHANGEPOINT_PRIOR_SCALE")
    PROPHET_YEARLY_SEASONALITY: bool = Field(default=True, env="PROPHET_YEARLY_SEASONALITY")
    PROPHET_WEEKLY_SEASONALITY: bool = Field(default=True, env="PROPHET_WEEKLY_SEASONALITY")
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# 전역 설정 인스턴스
settings = Settings()

# 환경별 설정
if os.getenv("ENVIRONMENT") == "development":
    settings.DEBUG = True
    settings.LOG_LEVEL = "DEBUG"
elif os.getenv("ENVIRONMENT") == "production":
    settings.DEBUG = False
    settings.LOG_LEVEL = "WARNING"
