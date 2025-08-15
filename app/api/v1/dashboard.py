#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
K-ETS Dashboard API 엔드포인트
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any
import logging

from app.core.security import get_current_user
from app.services.dashboard_service import DashboardService
from app.models.schemas import DashboardData, ChartData, MetricData

logger = logging.getLogger(__name__)
router = APIRouter()

# 대시보드 서비스 인스턴스
dashboard_service = DashboardService()

@router.get("/dashboard/overview", response_model=Dict[str, Any])
async def get_dashboard_overview(
    current_user: dict = Depends(get_current_user)
):
    """대시보드 개요 데이터 조회"""
    try:
        overview_data = await dashboard_service.get_overview_data()
        return {
            "success": True,
            "data": overview_data,
            "timestamp": dashboard_service.get_current_timestamp()
        }
    except Exception as e:
        logger.error(f"대시보드 개요 조회 오류: {e}")
        raise HTTPException(status_code=500, detail="대시보드 데이터 조회 실패")

@router.get("/dashboard/metrics", response_model=List[MetricData])
async def get_dashboard_metrics(
    metric_type: Optional[str] = Query(None, description="메트릭 타입"),
    current_user: dict = Depends(get_current_user)
):
    """대시보드 메트릭 데이터 조회"""
    try:
        metrics = await dashboard_service.get_metrics(metric_type)
        return metrics
    except Exception as e:
        logger.error(f"메트릭 조회 오류: {e}")
        raise HTTPException(status_code=500, detail="메트릭 데이터 조회 실패")

@router.get("/dashboard/charts/{chart_type}", response_model=ChartData)
async def get_chart_data(
    chart_type: str,
    start_date: Optional[str] = Query(None, description="시작 날짜 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="종료 날짜 (YYYY-MM-DD)"),
    current_user: dict = Depends(get_current_user)
):
    """차트 데이터 조회"""
    try:
        chart_data = await dashboard_service.get_chart_data(
            chart_type, start_date, end_date
        )
        return chart_data
    except Exception as e:
        logger.error(f"차트 데이터 조회 오류: {e}")
        raise HTTPException(status_code=500, detail="차트 데이터 조회 실패")

@router.get("/dashboard/trends", response_model=Dict[str, Any])
async def get_trend_analysis(
    trend_type: str = Query(..., description="트렌드 타입 (carbon, power, market)"),
    period: str = Query("30d", description="분석 기간 (7d, 30d, 90d, 1y)"),
    current_user: dict = Depends(get_current_user)
):
    """트렌드 분석 데이터 조회"""
    try:
        trend_data = await dashboard_service.get_trend_analysis(trend_type, period)
        return {
            "success": True,
            "trend_type": trend_type,
            "period": period,
            "data": trend_data
        }
    except Exception as e:
        logger.error(f"트렌드 분석 오류: {e}")
        raise HTTPException(status_code=500, detail="트렌드 분석 실패")

@router.get("/dashboard/alerts", response_model=List[Dict[str, Any]])
async def get_alerts(
    alert_level: Optional[str] = Query(None, description="알림 레벨 (info, warning, critical)"),
    current_user: dict = Depends(get_current_user)
):
    """대시보드 알림 조회"""
    try:
        alerts = await dashboard_service.get_alerts(alert_level)
        return alerts
    except Exception as e:
        logger.error(f"알림 조회 오류: {e}")
        raise HTTPException(status_code=500, detail="알림 데이터 조회 실패")

@router.post("/dashboard/refresh")
async def refresh_dashboard_data(
    current_user: dict = Depends(get_current_user)
):
    """대시보드 데이터 새로고침"""
    try:
        result = await dashboard_service.refresh_data()
        return {
            "success": True,
            "message": "대시보드 데이터 새로고침 완료",
            "timestamp": dashboard_service.get_current_timestamp()
        }
    except Exception as e:
        logger.error(f"데이터 새로고침 오류: {e}")
        raise HTTPException(status_code=500, detail="데이터 새로고침 실패")

@router.get("/dashboard/status")
async def get_dashboard_status():
    """대시보드 상태 확인 (인증 불필요)"""
    try:
        status = await dashboard_service.get_status()
        return {
            "status": "healthy",
            "service": "K-ETS Dashboard",
            "version": "1.0.0",
            "components": status
        }
    except Exception as e:
        logger.error(f"상태 확인 오류: {e}")
        return {
            "status": "unhealthy",
            "service": "K-ETS Dashboard",
            "error": str(e)
        }

@router.get("/dashboard/export")
async def export_dashboard_data(
    export_format: str = Query("csv", description="내보내기 형식 (csv, excel, json)"),
    data_type: str = Query("overview", description="데이터 타입"),
    current_user: dict = Depends(get_current_user)
):
    """대시보드 데이터 내보내기"""
    try:
        export_result = await dashboard_service.export_data(export_format, data_type)
        return JSONResponse(
            content=export_result,
            headers={"Content-Disposition": f"attachment; filename=dashboard_{data_type}.{export_format}"}
        )
    except Exception as e:
        logger.error(f"데이터 내보내기 오류: {e}")
        raise HTTPException(status_code=500, detail="데이터 내보내기 실패")
