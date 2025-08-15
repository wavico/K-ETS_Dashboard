#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
챗봇 API 엔드포인트
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional, Any, Dict
import logging

from app.agents.chatbot_agent import ChatbotAgent
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()

# 전역 챗봇 에이전트 인스턴스
chatbot_agent: Optional[ChatbotAgent] = None

def get_chatbot_agent() -> ChatbotAgent:
    """챗봇 에이전트 의존성 주입"""
    global chatbot_agent
    if chatbot_agent is None:
        try:
            chatbot_agent = ChatbotAgent()
        except Exception as e:
            logger.error(f"챗봇 에이전트 초기화 실패: {e}")
            raise HTTPException(status_code=500, detail="챗봇 서비스를 사용할 수 없습니다")
    return chatbot_agent

class ChatRequest(BaseModel):
    """채팅 요청 모델"""
    query: str

class ChatResponse(BaseModel):
    """채팅 응답 모델"""
    query: str
    response: str
    timestamp: str
    visualization: Optional[Any] = None
    
class ChatHistoryResponse(BaseModel):
    """채팅 히스토리 응답 모델"""
    history: List[Dict[str, Any]]
    total_count: int

@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    agent: ChatbotAgent = Depends(get_chatbot_agent)
):
    """AI 챗봇과 대화"""
    try:
        response, visualization = agent.ask(request.query)
        
        # 최근 히스토리에서 응답 정보 가져오기
        recent_chat = agent.get_chat_history(limit=1)
        if recent_chat:
            query, response_text, timestamp, viz = recent_chat[-1]
            return ChatResponse(
                query=query,
                response=response_text,
                timestamp=timestamp,
                visualization=viz
            )
        else:
            raise HTTPException(status_code=500, detail="응답 생성에 실패했습니다")
            
    except Exception as e:
        logger.error(f"챗봇 응답 생성 실패: {e}")
        raise HTTPException(status_code=500, detail=f"오류가 발생했습니다: {str(e)}")

@router.get("/chat/history", response_model=ChatHistoryResponse)
async def get_chat_history(
    limit: Optional[int] = None,
    agent: ChatbotAgent = Depends(get_chatbot_agent)
):
    """채팅 히스토리 조회"""
    try:
        history = agent.get_chat_history(limit=limit)
        
        # 히스토리를 딕셔너리 형태로 변환
        formatted_history = []
        for item in history:
            if len(item) == 4:
                query, response, timestamp, visualization = item
                formatted_history.append({
                    "query": query,
                    "response": response,
                    "timestamp": timestamp,
                    "visualization": visualization
                })
            elif len(item) == 3:
                query, response, timestamp = item
                formatted_history.append({
                    "query": query,
                    "response": response,
                    "timestamp": timestamp,
                    "visualization": None
                })
        
        return ChatHistoryResponse(
            history=formatted_history,
            total_count=len(agent.get_chat_history())
        )
        
    except Exception as e:
        logger.error(f"채팅 히스토리 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"히스토리 조회에 실패했습니다: {str(e)}")

@router.delete("/chat/history")
async def clear_chat_history(
    agent: ChatbotAgent = Depends(get_chatbot_agent)
):
    """채팅 히스토리 초기화"""
    try:
        agent.clear_history()
        return {"message": "채팅 히스토리가 초기화되었습니다"}
        
    except Exception as e:
        logger.error(f"채팅 히스토리 초기화 실패: {e}")
        raise HTTPException(status_code=500, detail=f"히스토리 초기화에 실패했습니다: {str(e)}")

@router.get("/chat/examples")
async def get_example_queries(
    agent: ChatbotAgent = Depends(get_chatbot_agent)
):
    """예시 질문 목록 조회"""
    try:
        examples = agent.get_example_queries()
        return {"examples": examples}
        
    except Exception as e:
        logger.error(f"예시 질문 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"예시 질문 조회에 실패했습니다: {str(e)}")

@router.get("/chat/data-info")
async def get_data_info(
    agent: ChatbotAgent = Depends(get_chatbot_agent)
):
    """데이터 정보 조회"""
    try:
        data_info = agent.get_data_info()
        return {"data_info": data_info}
        
    except Exception as e:
        logger.error(f"데이터 정보 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"데이터 정보 조회에 실패했습니다: {str(e)}")

@router.get("/chat/health")
async def chatbot_health_check():
    """챗봇 서비스 헬스 체크"""
    try:
        # 챗봇 에이전트 초기화 테스트
        agent = get_chatbot_agent()
        return {
            "status": "healthy",
            "service": "chatbot",
            "agent_loaded": agent is not None
        }
        
    except Exception as e:
        logger.error(f"챗봇 헬스 체크 실패: {e}")
        return {
            "status": "unhealthy", 
            "service": "chatbot",
            "error": str(e)
        }