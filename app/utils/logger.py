#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
K-ETS Dashboard 로깅 유틸리티
"""

import logging
import logging.handlers
import os
from datetime import datetime
from typing import Optional

def setup_logger(
    name: str,
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
) -> logging.Logger:
    """로거 설정"""
    
    # 로거 생성
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # 이미 핸들러가 설정되어 있으면 중복 설정 방지
    if logger.handlers:
        return logger
    
    # 포맷터 설정
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 콘솔 핸들러
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 파일 핸들러 (지정된 경우)
    if log_file:
        # 로그 디렉토리 생성
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # 로테이팅 파일 핸들러
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

def get_logger(name: str) -> logging.Logger:
    """로거 가져오기"""
    return logging.getLogger(name)

# 기본 로거 설정
default_logger = setup_logger("kets_dashboard")

# 로그 레벨별 함수들
def log_info(message: str, logger: Optional[logging.Logger] = None):
    """정보 로그"""
    if logger is None:
        logger = default_logger
    logger.info(message)

def log_warning(message: str, logger: Optional[logging.Logger] = None):
    """경고 로그"""
    if logger is None:
        logger = default_logger
    logger.warning(message)

def log_error(message: str, logger: Optional[logging.Logger] = None):
    """오류 로그"""
    if logger is None:
        logger = default_logger
    logger.error(message)

def log_debug(message: str, logger: Optional[logging.Logger] = None):
    """디버그 로그"""
    if logger is None:
        logger = default_logger
    logger.debug(message)

def log_critical(message: str, logger: Optional[logging.Logger] = None):
    """치명적 오류 로그"""
    if logger is None:
        logger = default_logger
    logger.critical(message)

# 성능 측정 데코레이터
def log_execution_time(logger: Optional[logging.Logger] = None):
    """함수 실행 시간 로깅 데코레이터"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = datetime.now()
            result = func(*args, **kwargs)
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            
            if logger:
                logger.info(f"{func.__name__} 실행 시간: {execution_time:.4f}초")
            else:
                default_logger.info(f"{func.__name__} 실행 시간: {execution_time:.4f}초")
            
            return result
        return wrapper
    return decorator

# 로그 컨텍스트 매니저
class LogContext:
    """로그 컨텍스트 매니저"""
    
    def __init__(self, logger: logging.Logger, context: str):
        self.logger = logger
        self.context = context
    
    def __enter__(self):
        self.logger.info(f"🚀 {self.context} 시작")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.logger.info(f"✅ {self.context} 완료")
        else:
            self.logger.error(f"❌ {self.context} 실패: {exc_val}")
        return False
