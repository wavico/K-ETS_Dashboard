"""
AI 챗봇 에이전트
FastAPI용으로 수정된 버전
"""

import os
from datetime import datetime
from typing import Optional, List, Tuple, Any
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

try:
    from app.agents.enhanced_rag_agent import EnhancedCarbonRAGAgent
except ImportError as e:
    print(f"향상된 RAG 에이전트 모듈을 불러올 수 없습니다: {e}")
    EnhancedCarbonRAGAgent = None

class ChatbotAgent:
    """FastAPI용 챗봇 에이전트 클래스"""
    
    def __init__(self):
        """에이전트 초기화"""
        if EnhancedCarbonRAGAgent is None:
            raise ImportError("향상된 RAG 에이전트를 불러올 수 없습니다")
        
        self.agent = EnhancedCarbonRAGAgent()
        self.chat_history: List[Tuple[str, str, str, Optional[Any]]] = []
    
    def get_data_info(self) -> str:
        """데이터 정보 반환"""
        try:
            return self.agent.get_available_data_info()
        except Exception as e:
            return f"데이터 정보를 가져올 수 없습니다: {e}"
    
    def ask(self, query: str) -> Tuple[str, Optional[Any]]:
        """질문 처리"""
        try:
            response, visualization = self.agent.ask(query)
            timestamp = datetime.now().strftime("%H:%M")
            
            # 채팅 히스토리에 추가
            if visualization:
                self.chat_history.append((query, response, timestamp, visualization))
            else:
                self.chat_history.append((query, response, timestamp))
            
            return response, visualization
        except Exception as e:
            error_msg = f"오류가 발생했습니다: {e}"
            timestamp = datetime.now().strftime("%H:%M")
            self.chat_history.append((query, error_msg, timestamp))
            return error_msg, None
    
    def get_chat_history(self, limit: Optional[int] = None) -> List[Tuple[str, str, str, Optional[Any]]]:
        """채팅 히스토리 반환"""
        if limit:
            return self.chat_history[-limit:]
        return self.chat_history
    
    def clear_history(self):
        """채팅 히스토리 초기화"""
        self.chat_history = []
    
    def get_example_queries(self) -> List[str]:
        """예시 질문 목록 반환"""
        return [
            "📈 총배출량 변화",
            "🏭 산업별 비교", 
            "📊 연도별 추이",
            "🔍 최대 배출 분야"
        ] 