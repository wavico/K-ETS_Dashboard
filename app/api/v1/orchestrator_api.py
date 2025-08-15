#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
에이전트 오케스트레이터 API 엔드포인트
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
import logging

from app.agents.orchestrator import AgentOrchestrator
from app.models.agent_response import AgentResponse
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()

# 전역 오케스트레이터 인스턴스
orchestrator: Optional[AgentOrchestrator] = None

def get_orchestrator() -> AgentOrchestrator:
    """오케스트레이터 의존성 주입"""
    global orchestrator
    if orchestrator is None:
        try:
            orchestrator = AgentOrchestrator()
        except Exception as e:
            logger.error(f"오케스트레이터 초기화 실패: {e}")
            raise HTTPException(status_code=500, detail="에이전트 서비스를 사용할 수 없습니다")
    return orchestrator

class ProcessRequest(BaseModel):
    """처리 요청 모델"""
    message: str
    context: Optional[Dict[str, Any]] = None
    user_id: Optional[str] = None

class DashboardAnalysisRequest(BaseModel):
    """대시보드 분석 요청 모델"""
    dashboard_state: Dict[str, Any]
    analysis_types: Optional[List[str]] = None

@router.post("/process", response_model=AgentResponse)
async def process_user_input(request: ProcessRequest):
    """사용자 입력 처리"""
    try:
        agent_orchestrator = get_orchestrator()
        
        response = await agent_orchestrator.process_user_input(
            message=request.message,
            context=request.context or {}
        )
        
        return response
        
    except Exception as e:
        logger.error(f"사용자 입력 처리 실패: {e}")
        raise HTTPException(status_code=500, detail=f"처리 중 오류가 발생했습니다: {str(e)}")

@router.post("/analyze-dashboard")
async def analyze_dashboard(request: DashboardAnalysisRequest):
    """대시보드 종합 분석"""
    try:
        agent_orchestrator = get_orchestrator()
        
        analysis_result = await agent_orchestrator.analyze_dashboard(
            request.dashboard_state
        )
        
        return {
            "analysis_result": analysis_result,
            "timestamp": agent_orchestrator.get_timestamp(),
            "status": "completed"
        }
        
    except Exception as e:
        logger.error(f"대시보드 분석 실패: {e}")
        raise HTTPException(status_code=500, detail=f"대시보드 분석에 실패했습니다: {str(e)}")

@router.get("/status")
async def get_orchestrator_status():
    """오케스트레이터 상태 조회"""
    try:
        agent_orchestrator = get_orchestrator()
        status = await agent_orchestrator.get_status()
        return status
        
    except Exception as e:
        logger.error(f"상태 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"상태 조회에 실패했습니다: {str(e)}")

@router.get("/capabilities")
async def get_capabilities():
    """에이전트 기능 조회"""
    try:
        agent_orchestrator = get_orchestrator()
        capabilities = await agent_orchestrator.get_capabilities()
        return capabilities
        
    except Exception as e:
        logger.error(f"기능 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"기능 조회에 실패했습니다: {str(e)}")

@router.get("/history")
async def get_processing_history(
    user_id: Optional[str] = None,
    limit: int = 10
):
    """처리 이력 조회"""
    try:
        agent_orchestrator = get_orchestrator()
        history = await agent_orchestrator.get_history(user_id=user_id, limit=limit)
        return {
            "history": history,
            "count": len(history)
        }
        
    except Exception as e:
        logger.error(f"이력 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"이력 조회에 실패했습니다: {str(e)}")

@router.get("/conversation-history")
async def get_conversation_history(limit: int = 20):
    """대화 이력 조회"""
    try:
        agent_orchestrator = get_orchestrator()
        
        # 최근 대화 이력 반환
        recent_conversations = agent_orchestrator.conversation_history[-limit:] if limit else agent_orchestrator.conversation_history
        
        return {
            "conversations": recent_conversations,
            "total_count": len(agent_orchestrator.conversation_history),
            "returned_count": len(recent_conversations)
        }
        
    except Exception as e:
        logger.error(f"대화 이력 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"대화 이력 조회에 실패했습니다: {str(e)}")

class FeedbackRequest(BaseModel):
    """피드백 요청 모델"""
    feedback: Dict[str, Any]
    user_id: Optional[str] = None

@router.post("/feedback")
async def submit_feedback(request: FeedbackRequest):
    """피드백 제출"""
    try:
        agent_orchestrator = get_orchestrator()
        result = await agent_orchestrator.submit_feedback(
            feedback=request.feedback,
            user_id=request.user_id
        )
        return result
        
    except Exception as e:
        logger.error(f"피드백 제출 실패: {e}")
        raise HTTPException(status_code=500, detail=f"피드백 제출에 실패했습니다: {str(e)}")

@router.post("/agents/{agent_name}/process")
async def process_with_specific_agent(
    agent_name: str,
    request: ProcessRequest
):
    """특정 에이전트로 직접 처리"""
    try:
        agent_orchestrator = get_orchestrator()
        
        # 에이전트 존재 확인
        if agent_name not in agent_orchestrator.agents:
            raise HTTPException(
                status_code=404, 
                detail=f"에이전트 '{agent_name}'을 찾을 수 없습니다"
            )
        
        agent = agent_orchestrator.agents[agent_name]
        
        # 에이전트 직접 호출
        if hasattr(agent, 'process'):
            response = await agent.process(request.message, request.context or {})
            return response
        else:
            # 기존 방식 호출
            context = request.context or {}
            if agent_name == "prediction":
                result = await agent_orchestrator.make_prediction(
                    target_column=context.get("target_column", "emission"),
                    days_ahead=context.get("days_ahead", 7),
                    user_id=request.user_id
                )
            elif agent_name == "analysis":
                result = await agent_orchestrator.analyze_data(
                    analysis_type=context.get("analysis_type", "trend"),
                    parameters=context,
                    user_id=request.user_id
                )
            elif agent_name == "report":
                result = await agent_orchestrator.generate_report(
                    report_type=context.get("report_type", "summary"),
                    parameters=context,
                    user_id=request.user_id
                )
            elif agent_name == "strategy":
                result = await agent_orchestrator.generate_strategy(
                    strategy_type=context.get("strategy_type", "emission_reduction"),
                    parameters=context,
                    user_id=request.user_id
                )
            else:
                raise HTTPException(status_code=400, detail="지원되지 않는 에이전트입니다")
            
            return {"result": result}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"에이전트 '{agent_name}' 처리 실패: {e}")
        raise HTTPException(status_code=500, detail=f"처리 중 오류가 발생했습니다: {str(e)}")

@router.get("/agents")
async def list_agents():
    """사용 가능한 에이전트 목록"""
    try:
        agent_orchestrator = get_orchestrator()
        
        agents_info = {}
        for name, agent in agent_orchestrator.agents.items():
            try:
                if hasattr(agent, 'get_status'):
                    status = agent.get_status()
                else:
                    status = {"status": "available"}
                
                if hasattr(agent, 'get_capabilities'):
                    capabilities = agent.get_capabilities()
                else:
                    capabilities = ["기본 기능"]
                
                agents_info[name] = {
                    "name": name,
                    "status": status,
                    "capabilities": capabilities,
                    "type": getattr(agent, 'agent_type', name)
                }
            except Exception as e:
                agents_info[name] = {
                    "name": name,
                    "status": {"status": "error", "error": str(e)},
                    "capabilities": [],
                    "type": name
                }
        
        return {
            "agents": agents_info,
            "total_count": len(agents_info)
        }
        
    except Exception as e:
        logger.error(f"에이전트 목록 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"에이전트 목록 조회에 실패했습니다: {str(e)}")

@router.post("/cleanup")
async def cleanup_orchestrator():
    """오케스트레이터 정리"""
    try:
        agent_orchestrator = get_orchestrator()
        await agent_orchestrator.cleanup()
        
        return {"message": "오케스트레이터가 성공적으로 정리되었습니다"}
        
    except Exception as e:
        logger.error(f"오케스트레이터 정리 실패: {e}")
        raise HTTPException(status_code=500, detail=f"정리 중 오류가 발생했습니다: {str(e)}")

@router.get("/health")
async def orchestrator_health_check():
    """오케스트레이터 헬스 체크"""
    try:
        # 오케스트레이터 초기화 테스트
        agent_orchestrator = get_orchestrator()
        status = await agent_orchestrator.get_status()
        
        return {
            "status": "healthy",
            "service": "orchestrator",
            "orchestrator_status": status.get("orchestrator", "unknown"),
            "active_agents": len(agent_orchestrator.agents),
            "total_tasks": len(agent_orchestrator.task_history)
        }
        
    except Exception as e:
        logger.error(f"오케스트레이터 헬스 체크 실패: {e}")
        return {
            "status": "unhealthy",
            "service": "orchestrator",
            "error": str(e)
        }