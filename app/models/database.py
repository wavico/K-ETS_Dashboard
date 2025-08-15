#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
K-ETS Dashboard SQLAlchemy 데이터베이스 모델
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, Float, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime

Base = declarative_base()

class User(Base):
    """사용자 테이블"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    full_name = Column(String(100), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    permissions = Column(JSON, default=list)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class DataFile(Base):
    """데이터 파일 테이블"""
    __tablename__ = "data_files"
    
    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(String(100), unique=True, index=True, nullable=False)
    filename = Column(String(255), nullable=False)
    data_type = Column(String(50), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)
    user_id = Column(Integer, nullable=False)
    upload_status = Column(String(50), default="uploaded")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class AnalysisTask(Base):
    """분석 작업 테이블"""
    __tablename__ = "analysis_tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String(100), unique=True, index=True, nullable=False)
    task_type = Column(String(50), nullable=False)
    parameters = Column(JSON, nullable=False)
    status = Column(String(50), default="pending")
    result = Column(JSON, nullable=True)
    user_id = Column(Integer, nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class PredictionResult(Base):
    """예측 결과 테이블"""
    __tablename__ = "prediction_results"
    
    id = Column(Integer, primary_key=True, index=True)
    prediction_id = Column(String(100), unique=True, index=True, nullable=False)
    target_column = Column(String(100), nullable=False)
    days_ahead = Column(Integer, nullable=False)
    prediction_data = Column(JSON, nullable=False)
    model_info = Column(JSON, nullable=True)
    user_id = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Report(Base):
    """리포트 테이블"""
    __tablename__ = "reports"
    
    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(String(100), unique=True, index=True, nullable=False)
    report_type = Column(String(50), nullable=False)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    parameters = Column(JSON, nullable=True)
    user_id = Column(Integer, nullable=False)
    generated_at = Column(DateTime(timezone=True), server_default=func.now())

class SystemLog(Base):
    """시스템 로그 테이블"""
    __tablename__ = "system_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    level = Column(String(20), nullable=False)
    message = Column(Text, nullable=False)
    module = Column(String(100), nullable=True)
    user_id = Column(Integer, nullable=True)
    ip_address = Column(String(45), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class UserSession(Base):
    """사용자 세션 테이블"""
    __tablename__ = "user_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), unique=True, index=True, nullable=False)
    user_id = Column(Integer, nullable=False)
    token = Column(String(500), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_activity = Column(DateTime(timezone=True), onupdate=func.now())
