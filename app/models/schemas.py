#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
K-ETS Dashboard Pydantic 스키마
"""

from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime

class DashboardData(BaseModel):
    """대시보드 데이터 스키마"""
    carbon_emissions: Dict[str, Any]
    renewable_energy: Dict[str, Any]
    energy_efficiency: Dict[str, Any]

class ChartData(BaseModel):
    """차트 데이터 스키마"""
    chart_type: str
    data: List[Dict[str, Any]]

class MetricData(BaseModel):
    """메트릭 데이터 스키마"""
    name: str
    value: float
    unit: str
    change: float
    trend: str

class AgentRequest(BaseModel):
    """에이전트 요청 스키마"""
    analysis_type: str = Field(..., description="분석 타입")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="분석 파라미터")

class AgentResponse(BaseModel):
    """에이전트 응답 스키마"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class PredictionRequest(BaseModel):
    """예측 요청 스키마"""
    target_column: str = Field(..., description="예측 대상 컬럼")
    days_ahead: int = Field(default=7, description="예측 일수")

class DataUploadResponse(BaseModel):
    """데이터 업로드 응답 스키마"""
    success: bool
    file_id: str
    filename: str
    data_type: str
    message: str

class DataProcessRequest(BaseModel):
    """데이터 처리 요청 스키마"""
    file_id: str = Field(..., description="파일 ID")
    analysis_type: str = Field(..., description="분석 타입")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="분석 파라미터")

class User(BaseModel):
    """사용자 스키마"""
    username: str
    email: str
    full_name: str
    permissions: List[str] = []

class LoginRequest(BaseModel):
    """로그인 요청 스키마"""
    username: str
    password: str

class LoginResponse(BaseModel):
    """로그인 응답 스키마"""
    access_token: str
    token_type: str = "bearer"
    user: User

class HealthCheck(BaseModel):
    """헬스체크 스키마"""
    status: str
    service: str
    timestamp: datetime
    version: str = "1.0.0"
