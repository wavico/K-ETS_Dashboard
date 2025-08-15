#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
K-ETS Dashboard 데이터베이스 연결 관리
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from contextlib import contextmanager
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

# 데이터베이스 엔진 생성
if settings.DATABASE_URL.startswith("sqlite"):
    # SQLite용 엔진 (개발/테스트용)
    engine = create_engine(
        settings.DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=settings.DEBUG
    )
else:
    # PostgreSQL/MySQL용 엔진 (프로덕션용)
    engine = create_engine(
        settings.DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=300,
        echo=settings.DEBUG
    )

# 세션 팩토리 생성
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 베이스 클래스
Base = declarative_base()

def get_db() -> Session:
    """데이터베이스 세션 가져오기"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@contextmanager
def get_db_context():
    """컨텍스트 매니저로 데이터베이스 세션 관리"""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"데이터베이스 오류: {e}")
        raise
    finally:
        db.close()

def init_db():
    """데이터베이스 초기화 (테이블 생성)"""
    try:
        # 모든 모델 임포트
        from app.models import database
        
        # 테이블 생성
        Base.metadata.create_all(bind=engine)
        logger.info("✅ 데이터베이스 테이블 생성 완료")
        
    except Exception as e:
        logger.error(f"❌ 데이터베이스 초기화 오류: {e}")
        raise

def check_db_connection():
    """데이터베이스 연결 상태 확인"""
    try:
        with engine.connect() as connection:
            result = connection.execute("SELECT 1")
            logger.info("✅ 데이터베이스 연결 성공")
            return True
    except Exception as e:
        logger.error(f"❌ 데이터베이스 연결 실패: {e}")
        return False

# 데이터베이스 헬스체크
def health_check():
    """데이터베이스 헬스체크"""
    return {
        "database": "healthy" if check_db_connection() else "unhealthy",
        "url": settings.DATABASE_URL.split("://")[0] if "://" in settings.DATABASE_URL else "unknown"
    }
