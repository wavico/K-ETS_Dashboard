#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
K-ETS Dashboard AI 에이전트 API 엔드포인트
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Body
from typing import List, Optional, Dict, Any
import logging

from app.core.security import get_current_user
from app.agents.orchestrator import AgentOrchestrator
from app.models.schemas import AgentRequest, AgentResponse, PredictionRequest

logger = logging.getLogger(__name__)
router = APIRouter()

# 에이전트 오케스트레이터 인스턴스
agent_orchestrator = AgentOrchestrator()

@router.post("/agent/predict", response_model=Dict[str, Any])
async def make_prediction(
    request: PredictionRequest,
    current_user: dict = Depends(get_current_user)
):
    """AI 에이전트를 통한 예측 수행"""
    try:
        prediction_result = await agent_orchestrator.make_prediction(
            target_column=request.target_column,
            days_ahead=request.days_ahead,
            user_id=current_user.get("username")
        )
        
        return {
            "success": True,
            "prediction": prediction_result,
            "user": current_user.get("username"),
            "timestamp": agent_orchestrator.get_timestamp()
        }
    except Exception as e:
        logger.error(f"예측 수행 오류: {e}")
        raise HTTPException(status_code=500, detail=f"예측 수행 실패: {str(e)}")

@router.post("/agent/analyze", response_model=Dict[str, Any])
async def analyze_data(
    request: AgentRequest,
    current_user: dict = Depends(get_current_user)
):
    """AI 에이전트를 통한 데이터 분석"""
    try:
        analysis_result = await agent_orchestrator.analyze_data(
            analysis_type=request.analysis_type,
            parameters=request.parameters,
            user_id=current_user.get("username")
        )
        
        return {
            "success": True,
            "analysis": analysis_result,
            "user": current_user.get("username"),
            "timestamp": agent_orchestrator.get_timestamp()
        }
    except Exception as e:
        logger.error(f"데이터 분석 오류: {e}")
        raise HTTPException(status_code=500, detail=f"데이터 분석 실패: {str(e)}")

@router.post("/agent/generate-report", response_model=Dict[str, Any])
async def generate_report(
    request: AgentRequest,
    current_user: dict = Depends(get_current_user)
):
    """AI 에이전트를 통한 리포트 생성"""
    try:
        report_result = await agent_orchestrator.generate_report(
            report_type=request.analysis_type,
            parameters=request.parameters,
            user_id=current_user.get("username")
        )
        
        return {
            "success": True,
            "report": report_result,
            "user": current_user.get("username"),
            "timestamp": agent_orchestrator.get_timestamp()
        }
    except Exception as e:
        logger.error(f"리포트 생성 오류: {e}")
        raise HTTPException(status_code=500, detail=f"리포트 생성 실패: {str(e)}")

@router.post("/agent/strategy", response_model=Dict[str, Any])
async def generate_strategy(
    request: AgentRequest,
    current_user: dict = Depends(get_current_user)
):
    """AI 에이전트를 통한 전략 도출"""
    try:
        strategy_result = await agent_orchestrator.generate_strategy(
            strategy_type=request.analysis_type,
            parameters=request.parameters,
            user_id=current_user.get("username")
        )
        
        return {
            "success": True,
            "strategy": strategy_result,
            "user": current_user.get("username"),
            "timestamp": agent_orchestrator.get_timestamp()
        }
    except Exception as e:
        logger.error(f"전략 도출 오류: {e}")
        raise HTTPException(status_code=500, detail=f"전략 도출 실패: {str(e)}")

@router.get("/agent/status", response_model=Dict[str, Any])
async def get_agent_status(
    current_user: dict = Depends(get_current_user)
):
    """AI 에이전트 상태 확인"""
    try:
        status = await agent_orchestrator.get_status()
        return {
            "success": True,
            "status": status,
            "user": current_user.get("username")
        }
    except Exception as e:
        logger.error(f"에이전트 상태 확인 오류: {e}")
        raise HTTPException(status_code=500, detail="에이전트 상태 확인 실패")

@router.get("/agent/capabilities", response_model=Dict[str, Any])
async def get_agent_capabilities(
    current_user: dict = Depends(get_current_user)
):
    """AI 에이전트 기능 목록 조회"""
    try:
        capabilities = await agent_orchestrator.get_capabilities()
        return {
            "success": True,
            "capabilities": capabilities
        }
    except Exception as e:
        logger.error(f"에이전트 기능 조회 오류: {e}")
        raise HTTPException(status_code=500, detail="에이전트 기능 조회 실패")

@router.post("/agent/chat", response_model=Dict[str, Any])
async def chat_with_agent(
    message: str = Body(..., embed=True),
    context: Optional[Dict[str, Any]] = Body(None, embed=True),
    current_user: dict = Depends(get_current_user)
):
    """AI 에이전트와 대화"""
    try:
        chat_result = await agent_orchestrator.chat(
            message=message,
            context=context,
            user_id=current_user.get("username")
        )
        
        return {
            "success": True,
            "response": chat_result,
            "user": current_user.get("username"),
            "timestamp": agent_orchestrator.get_timestamp()
        }
    except Exception as e:
        logger.error(f"에이전트 대화 오류: {e}")
        raise HTTPException(status_code=500, detail=f"에이전트 대화 실패: {str(e)}")

@router.get("/agent/history", response_model=List[Dict[str, Any]])
async def get_agent_history(
    limit: int = Query(10, description="조회할 기록 수"),
    current_user: dict = Depends(get_current_user)
):
    """AI 에이전트 사용 기록 조회"""
    try:
        history = await agent_orchestrator.get_history(
            user_id=current_user.get("username"),
            limit=limit
        )
        return history
    except Exception as e:
        logger.error(f"에이전트 기록 조회 오류: {e}")
        raise HTTPException(status_code=500, detail="에이전트 기록 조회 실패")

@router.post("/agent/feedback")
async def submit_agent_feedback(
    feedback: Dict[str, Any] = Body(...),
    current_user: dict = Depends(get_current_user)
):
    """AI 에이전트 피드백 제출"""
    try:
        result = await agent_orchestrator.submit_feedback(
            feedback=feedback,
            user_id=current_user.get("username")
        )
        
        return {
            "success": True,
            "message": "피드백이 성공적으로 제출되었습니다.",
            "feedback_id": result.get("feedback_id")
        }
    except Exception as e:
        logger.error(f"피드백 제출 오류: {e}")
        raise HTTPException(status_code=500, detail="피드백 제출 실패")
