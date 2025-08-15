#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
에이전트 베이스 클래스
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
import asyncio
import time
import logging

from app.models.agent_response import AgentResponse
from app.core.config import settings

logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    """모든 에이전트의 베이스 클래스"""
    
    def __init__(self, agent_type: str):
        self.agent_type = agent_type
        self.llm = None  # 각 에이전트에서 구현
        self.tools = []  # 각 에이전트에서 정의
        self.processing_history = []
        
    @abstractmethod
    async def process(self, message: str, context: Dict[str, Any]) -> AgentResponse:
        """메시지 처리 (각 에이전트에서 구현 필요)"""
        pass
    
    @abstractmethod
    async def analyze_dashboard_section(self, dashboard_state: Dict) -> Dict[str, Any]:
        """대시보드 섹션 분석 (각 에이전트에서 구현 필요)"""
        pass
    
    def _initialize_llm(self):
        """LLM 초기화 (각 에이전트에서 구체적으로 구현)"""
        # 여기서는 기본 구조만 제공
        pass
    
    async def _measure_processing_time(self, func, *args, **kwargs):
        """처리 시간 측정"""
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            processing_time = time.time() - start_time
            return result, processing_time
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"{self.agent_type} 처리 중 오류: {e}")
            raise e
    
    def _update_processing_history(self, message: str, result: AgentResponse):
        """처리 이력 업데이트"""
        self.processing_history.append({
            "timestamp": result.timestamp,
            "message": message,
            "agent_type": self.agent_type,
            "processing_time": result.processing_time,
            "success": True
        })
        
        # 이력이 너무 길어지면 오래된 것 삭제
        if len(self.processing_history) > 100:
            self.processing_history = self.processing_history[-50:]
    
    async def _parse_intent(self, message: str) -> Dict[str, Any]:
        """메시지에서 의도 분석"""
        # 기본 키워드 기반 의도 분석
        intent = {
            "action": "unknown",
            "entities": [],
            "confidence": 0.0
        }
        
        message_lower = message.lower()
        
        # 분석 관련 키워드
        if any(word in message_lower for word in ['분석', '분석해', '조회', '확인', '보여줘']):
            intent["action"] = "analyze"
            intent["confidence"] = 0.8
            
        # 예측 관련 키워드
        elif any(word in message_lower for word in ['예측', '예상', '전망', '미래']):
            intent["action"] = "predict"
            intent["confidence"] = 0.8
            
        # 리포트 관련 키워드
        elif any(word in message_lower for word in ['리포트', '보고서', '요약', '정리']):
            intent["action"] = "report"
            intent["confidence"] = 0.8
            
        # 전략 관련 키워드
        elif any(word in message_lower for word in ['전략', '방안', '계획', '추천', '제안']):
            intent["action"] = "strategy"
            intent["confidence"] = 0.8
        
        return intent
    
    def _extract_entities(self, message: str) -> List[Dict[str, Any]]:
        """메시지에서 엔티티 추출"""
        entities = []
        message_lower = message.lower()
        
        # 연도 추출
        import re
        years = re.findall(r'\b(20\d{2})\b', message)
        for year in years:
            entities.append({
                "type": "year",
                "value": int(year),
                "text": year
            })
        
        # 부문 추출
        sectors = ['에너지', '산업공정', '농업', '폐기물', 'lulucf']
        for sector in sectors:
            if sector in message_lower:
                entities.append({
                    "type": "sector",
                    "value": sector,
                    "text": sector
                })
        
        return entities
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """처리 통계 조회"""
        if not self.processing_history:
            return {"total_requests": 0, "avg_processing_time": 0.0}
        
        total_requests = len(self.processing_history)
        avg_time = sum(h.get("processing_time", 0) for h in self.processing_history) / total_requests
        
        return {
            "total_requests": total_requests,
            "avg_processing_time": round(avg_time, 2),
            "recent_requests": self.processing_history[-10:] if total_requests > 10 else self.processing_history
        }