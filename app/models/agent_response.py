#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
에이전트 응답 모델
"""

from pydantic import BaseModel
from typing import Dict, List, Any, Optional
from datetime import datetime

class VisualizationData(BaseModel):
    """시각화 데이터 모델"""
    chart_type: str  # 'line', 'bar', 'pie', 'scatter' 등
    data: Dict[str, Any]
    config: Dict[str, Any] = {}
    title: Optional[str] = None
    description: Optional[str] = None

class MetricData(BaseModel):
    """메트릭 데이터 모델"""
    name: str
    value: float
    unit: Optional[str] = None
    change: Optional[float] = None
    change_type: Optional[str] = None  # 'increase', 'decrease', 'neutral'
    description: Optional[str] = None

class DashboardUpdate(BaseModel):
    """대시보드 업데이트 모델"""
    charts: Optional[List[VisualizationData]] = None
    metrics: Optional[List[MetricData]] = None
    tables: Optional[List[Dict[str, Any]]] = None
    alerts: Optional[List[str]] = None
    recommendations: Optional[List[str]] = None

class AgentResponse(BaseModel):
    """에이전트 응답 통합 모델"""
    # 기본 응답
    message: str
    agent_type: str
    timestamp: datetime = datetime.now()
    
    # 데이터
    data: Optional[Dict[str, Any]] = None
    
    # 시각화
    visualizations: Optional[List[VisualizationData]] = None
    
    # 대시보드 업데이트
    dashboard_updates: Optional[DashboardUpdate] = None
    
    # 메타데이터
    processing_time: Optional[float] = None
    confidence: Optional[float] = None
    sources: Optional[List[str]] = None
    
    # 추가 액션
    suggested_actions: Optional[List[str]] = None
    follow_up_questions: Optional[List[str]] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class AnalysisResponse(AgentResponse):
    """분석 에이전트 전용 응답"""
    analysis_type: str
    statistical_summary: Optional[Dict[str, Any]] = None
    trend_analysis: Optional[Dict[str, Any]] = None

class PredictionResponse(AgentResponse):
    """예측 에이전트 전용 응답"""
    prediction_period: str
    model_info: Optional[Dict[str, Any]] = None
    accuracy_metrics: Optional[Dict[str, Any]] = None
    forecast_data: Optional[Dict[str, Any]] = None

class ReportResponse(AgentResponse):
    """리포트 에이전트 전용 응답"""
    report_type: str
    sections: Optional[List[Dict[str, Any]]] = None
    executive_summary: Optional[str] = None

class StrategyResponse(AgentResponse):
    """전략 에이전트 전용 응답"""
    strategy_type: str
    recommendations: List[str]
    risk_assessment: Optional[Dict[str, Any]] = None
    implementation_plan: Optional[List[Dict[str, Any]]] = None

# 웹소켓 메시지 모델들
class WebSocketMessage(BaseModel):
    """웹소켓 메시지 기본 모델"""
    type: str
    data: Dict[str, Any]
    timestamp: datetime = datetime.now()

class ChatMessage(WebSocketMessage):
    """채팅 메시지"""
    text: str
    context: Optional[Dict[str, Any]] = None
    user_id: Optional[str] = None

class DashboardUpdateMessage(WebSocketMessage):
    """대시보드 업데이트 메시지"""
    updates: DashboardUpdate

class SystemMessage(WebSocketMessage):
    """시스템 메시지"""
    level: str  # 'info', 'warning', 'error'
    message: str