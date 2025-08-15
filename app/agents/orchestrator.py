#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
K-ETS Dashboard 멀티 에이전트 오케스트레이터
"""

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging
import uuid
import time

from app.agents.prediction_agent import PredictionAgent
from app.agents.analysis_agent import AnalysisAgent  
from app.agents.report_agent import ReportAgent
from app.agents.strategy_agent import StrategyAgent
from app.agents.chatbot_agent import ChatbotAgent
from app.models.agent_response import AgentResponse, DashboardUpdate
from app.utils.logger import get_logger

logger = get_logger(__name__)

class AgentOrchestrator:
    """멀티 AI 에이전트 조율 및 관리"""
    
    def __init__(self):
        """오케스트레이터 초기화"""
        self.agents = {}
        self.conversation_history = []
        self.task_history = []
        self.active_tasks = {}
        
        # 에이전트 초기화
        self._initialize_agents()
        
        logger.info("🚀 AI 에이전트 오케스트레이터 초기화 완료")
    
    def _initialize_agents(self):
        """에이전트들 초기화"""
        try:
            # 분석 에이전트  
            self.agents['analysis'] = AnalysisAgent()
            logger.info("✅ 분석 에이전트 초기화 완료")
            
            # 예측 에이전트
            self.agents['prediction'] = PredictionAgent()
            logger.info("✅ 예측 에이전트 초기화 완료")
            
            # 리포트 에이전트
            self.agents['report'] = ReportAgent()
            logger.info("✅ 리포트 에이전트 초기화 완료")
            
            # 전략 에이전트
            self.agents['strategy'] = StrategyAgent()
            logger.info("✅ 전략 에이전트 초기화 완료")
            
            # 챗봇 에이전트
            self.agents['chatbot'] = ChatbotAgent()
            logger.info("✅ 챗봇 에이전트 초기화 완료")
            
        except Exception as e:
            logger.error(f"❌ 에이전트 초기화 실패: {e}")
            raise
    
    async def process_user_input(self, message: str, context: Dict = None) -> AgentResponse:
        """사용자 입력 처리 및 적절한 에이전트 선택"""
        start_time = time.time()
        
        if context is None:
            context = {}
            
        try:
            # 1. 의도 분석
            intent = await self._analyze_intent(message)
            
            # 2. 적절한 에이전트 선택
            agent = self._select_agent(intent)
            
            # 3. 에이전트 실행
            result = await agent.process(message, context)
            
            # 4. 처리 시간 업데이트
            result.processing_time = time.time() - start_time
            
            # 5. 대화 히스토리 업데이트
            self.conversation_history.append({
                'user_input': message,
                'agent_used': agent.__class__.__name__,
                'intent': intent,
                'result': result.dict(),
                'timestamp': datetime.now().isoformat()
            })
            
            return result
            
        except Exception as e:
            logger.error(f"사용자 입력 처리 실패: {e}")
            
            # 오류 응답 생성
            error_response = AgentResponse(
                message=f"죄송합니다. 처리 중 오류가 발생했습니다: {str(e)}",
                agent_type="orchestrator",
                processing_time=time.time() - start_time
            )
            
            return error_response
    
    async def _analyze_intent(self, message: str) -> Dict[str, Any]:
        """메시지에서 의도 분석"""
        message_lower = message.lower()
        
        # 키워드 기반 의도 분석
        if any(word in message_lower for word in ['예측', '예상', '전망', '미래', '일', '주', '개월', 'prophet']):
            return {"action": "predict", "confidence": 0.9}
        elif any(word in message_lower for word in ['분석', '조회', '확인', '보여줘']):
            return {"action": "analyze", "confidence": 0.9}
        elif any(word in message_lower for word in ['리포트', '보고서', '요약']):
            return {"action": "report", "confidence": 0.9}
        elif any(word in message_lower for word in ['전략', '방안', '계획', '추천']):
            return {"action": "strategy", "confidence": 0.9}
        else:
            return {"action": "chat", "confidence": 0.7}
    
    def _select_agent(self, intent: Dict[str, Any]):
        """의도에 따른 에이전트 선택"""
        action = intent.get("action", "chat")
        
        agent_mapping = {
            "predict": "prediction",
            "analyze": "analysis", 
            "report": "report",
            "strategy": "strategy",
            "chat": "chatbot"
        }
        
        agent_key = agent_mapping.get(action, "chatbot")
        return self.agents[agent_key]
    
    async def analyze_dashboard(self, dashboard_state: Dict) -> Dict:
        """대시보드 상태 종합 분석"""
        try:
            analysis_tasks = []
            
            # 여러 에이전트가 동시에 분석
            for agent_name, agent in self.agents.items():
                if hasattr(agent, 'analyze_dashboard_section'):
                    task = asyncio.create_task(
                        agent.analyze_dashboard_section(dashboard_state)
                    )
                    analysis_tasks.append((agent_name, task))
            
            # 결과 통합
            combined_analysis = await self._combine_analysis_results(analysis_tasks)
            return combined_analysis
            
        except Exception as e:
            logger.error(f"대시보드 분석 실패: {e}")
            return {"error": str(e)}
    
    async def _combine_analysis_results(self, analysis_tasks: List) -> Dict:
        """분석 결과 통합"""
        combined_result = {
            "analysis_summary": {},
            "recommendations": [],
            "insights": [],
            "dashboard_updates": {}
        }
        
        for agent_name, task in analysis_tasks:
            try:
                result = await task
                combined_result["analysis_summary"][agent_name] = result
                
                # 추천사항 병합
                if "recommendations" in result:
                    combined_result["recommendations"].extend(result["recommendations"])
                
                # 인사이트 병합  
                if "insights" in result:
                    combined_result["insights"].extend(result["insights"])
                    
            except Exception as e:
                logger.error(f"{agent_name} 분석 실패: {e}")
                combined_result["analysis_summary"][agent_name] = {"error": str(e)}
        
        return combined_result
    
    async def make_prediction(
        self, 
        target_column: str, 
        days_ahead: int = 7,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """예측 에이전트를 통한 예측 수행"""
        task_id = str(uuid.uuid4())
        
        try:
            logger.info(f"🔮 예측 작업 시작: {target_column} {days_ahead}일")
            
            # 예측 에이전트 호출
            prediction_result = self.agents["prediction"].predict(
                target_column=target_column,
                days_ahead=days_ahead
            )
            
            # 작업 기록 저장
            task_record = {
                "task_id": task_id,
                "type": "prediction",
                "user_id": user_id,
                "parameters": {
                    "target_column": target_column,
                    "days_ahead": days_ahead
                },
                "result": prediction_result,
                "status": "completed",
                "timestamp": datetime.now().isoformat()
            }
            
            self.task_history.append(task_record)
            
            logger.info(f"✅ 예측 작업 완료: {task_id}")
            return prediction_result
            
        except Exception as e:
            logger.error(f"❌ 예측 작업 실패: {e}")
            
            # 실패 기록 저장
            task_record = {
                "task_id": task_id,
                "type": "prediction",
                "user_id": user_id,
                "parameters": {
                    "target_column": target_column,
                    "days_ahead": days_ahead
                },
                "error": str(e),
                "status": "failed",
                "timestamp": datetime.now().isoformat()
            }
            
            self.task_history.append(task_record)
            
            raise
    
    async def analyze_data(
        self,
        analysis_type: str,
        parameters: Dict[str, Any],
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """분석 에이전트를 통한 데이터 분석"""
        task_id = str(uuid.uuid4())
        
        try:
            logger.info(f"📊 분석 작업 시작: {analysis_type}")
            
            # 분석 에이전트 호출
            analysis_result = await self.agents["analysis"].analyze(
                analysis_type=analysis_type,
                parameters=parameters
            )
            
            # 작업 기록 저장
            task_record = {
                "task_id": task_id,
                "type": "analysis",
                "user_id": user_id,
                "parameters": {
                    "analysis_type": analysis_type,
                    "parameters": parameters
                },
                "result": analysis_result,
                "status": "completed",
                "timestamp": datetime.now().isoformat()
            }
            
            self.task_history.append(task_record)
            
            logger.info(f"✅ 분석 작업 완료: {task_id}")
            return analysis_result
            
        except Exception as e:
            logger.error(f"❌ 분석 작업 실패: {e}")
            
            # 실패 기록 저장
            task_record = {
                "task_id": task_id,
                "type": "analysis",
                "user_id": user_id,
                "parameters": {
                    "analysis_type": analysis_type,
                    "parameters": parameters
                },
                "error": str(e),
                "status": "failed",
                "timestamp": datetime.now().isoformat()
            }
            
            self.task_history.append(task_record)
            
            raise
    
    async def generate_report(
        self,
        report_type: str,
        parameters: Dict[str, Any],
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """리포트 에이전트를 통한 리포트 생성"""
        task_id = str(uuid.uuid4())
        
        try:
            logger.info(f"📋 리포트 생성 시작: {report_type}")
            
            # 리포트 에이전트 호출
            report_result = await self.agents["report"].generate_report(
                report_type=report_type,
                parameters=parameters
            )
            
            # 작업 기록 저장
            task_record = {
                "task_id": task_id,
                "type": "report",
                "user_id": user_id,
                "parameters": {
                    "report_type": report_type,
                    "parameters": parameters
                },
                "result": report_result,
                "status": "completed",
                "timestamp": datetime.now().isoformat()
            }
            
            self.task_history.append(task_record)
            
            logger.info(f"✅ 리포트 생성 완료: {task_id}")
            return report_result
            
        except Exception as e:
            logger.error(f"❌ 리포트 생성 실패: {e}")
            
            # 실패 기록 저장
            task_record = {
                "task_id": task_id,
                "type": "report",
                "user_id": user_id,
                "parameters": {
                    "report_type": report_type,
                    "parameters": parameters
                },
                "error": str(e),
                "status": "failed",
                "timestamp": datetime.now().isoformat()
            }
            
            self.task_history.append(task_record)
            
            raise
    
    async def generate_strategy(
        self,
        strategy_type: str,
        parameters: Dict[str, Any],
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """전략 에이전트를 통한 전략 도출"""
        task_id = str(uuid.uuid4())
        
        try:
            logger.info(f"🎯 전략 도출 시작: {strategy_type}")
            
            # 전략 에이전트 호출
            strategy_result = await self.agents["strategy"].generate_strategy(
                strategy_type=strategy_type,
                parameters=parameters
            )
            
            # 작업 기록 저장
            task_record = {
                "task_id": task_id,
                "type": "strategy",
                "user_id": user_id,
                "parameters": {
                    "strategy_type": strategy_type,
                    "parameters": parameters
                },
                "result": strategy_result,
                "status": "completed",
                "timestamp": datetime.now().isoformat()
            }
            
            self.task_history.append(task_record)
            
            logger.info(f"✅ 전략 도출 완료: {task_id}")
            return strategy_result
            
        except Exception as e:
            logger.error(f"❌ 전략 도출 실패: {e}")
            
            # 실패 기록 저장
            task_record = {
                "task_id": task_id,
                "type": "strategy",
                "user_id": user_id,
                "parameters": {
                    "strategy_type": strategy_type,
                    "parameters": parameters
                },
                "error": str(e),
                "status": "failed",
                "timestamp": datetime.now().isoformat()
            }
            
            self.task_history.append(task_record)
            
            raise
    
    async def chat(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """AI 에이전트와의 대화"""
        try:
            logger.info(f"💬 채팅 요청: {message[:50]}...")
            
            # 메시지 타입에 따른 에이전트 선택 및 실행
            if any(word in message for word in ["예측", "예상", "전망", "미래", "일", "주", "개월", "prophet"]):
                agent_type = "prediction"
                # 예측 에이전트로 실제 처리
                result = await self.agents["prediction"].process(message, context or {})
                response = result.message
            elif any(word in message for word in ["분석", "조회", "확인", "보여줘"]):
                agent_type = "analysis"
                result = await self.agents["analysis"].process(message, context or {})
                response = result.message
            elif any(word in message for word in ["리포트", "보고서", "요약"]):
                agent_type = "report"
                result = await self.agents["report"].process(message, context or {})
                response = result.message
            elif any(word in message for word in ["전략", "방안", "계획", "추천"]):
                agent_type = "strategy"
                result = await self.agents["strategy"].process(message, context or {})
                response = result.message
            else:
                agent_type = "chatbot"
                result = await self.agents["chatbot"].process(message, context or {})
                response = result.message if hasattr(result, 'message') else str(result)
            
            return {
                "agent_type": agent_type,
                "response": response,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ 채팅 처리 실패: {e}")
            return {
                "agent_type": "error",
                "response": f"죄송합니다. 오류가 발생했습니다: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
    
    async def get_status(self) -> Dict[str, Any]:
        """오케스트레이터 상태 정보"""
        agent_status = {}
        
        for name, agent in self.agents.items():
            try:
                if hasattr(agent, 'get_status'):
                    agent_status[name] = agent.get_status()
                else:
                    agent_status[name] = {"status": "unknown"}
            except Exception as e:
                agent_status[name] = {"status": "error", "error": str(e)}
        
        return {
            "orchestrator": "running",
            "agents": agent_status,
            "total_tasks": len(self.task_history),
            "completed_tasks": len([t for t in self.task_history if t["status"] == "completed"]),
            "failed_tasks": len([t for t in self.task_history if t["status"] == "failed"])
        }
    
    async def get_capabilities(self) -> Dict[str, Any]:
        """에이전트 기능 목록"""
        capabilities = {}
        
        for name, agent in self.agents.items():
            try:
                if hasattr(agent, 'get_capabilities'):
                    capabilities[name] = agent.get_capabilities()
                else:
                    capabilities[name] = ["기본 기능"]
            except Exception as e:
                capabilities[name] = [f"오류: {str(e)}"]
        
        return capabilities
    
    async def get_history(
        self,
        user_id: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """작업 기록 조회"""
        if user_id:
            user_tasks = [t for t in self.task_history if t.get("user_id") == user_id]
            return user_tasks[-limit:]
        else:
            return self.task_history[-limit:]
    
    async def submit_feedback(
        self,
        feedback: Dict[str, Any],
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """피드백 제출"""
        feedback_id = str(uuid.uuid4())
        
        feedback_record = {
            "feedback_id": feedback_id,
            "user_id": user_id,
            "feedback": feedback,
            "timestamp": datetime.now().isoformat()
        }
        
        # 피드백 저장 (실제로는 데이터베이스에 저장)
        logger.info(f"📝 피드백 제출: {feedback_id}")
        
        return {
            "feedback_id": feedback_id,
            "message": "피드백이 성공적으로 제출되었습니다."
        }
    
    def get_timestamp(self) -> str:
        """현재 타임스탬프 반환"""
        return datetime.now().isoformat()
    
    async def cleanup(self):
        """오케스트레이터 정리"""
        logger.info("🧹 오케스트레이터 정리 중...")
        
        # 에이전트 정리
        for name, agent in self.agents.items():
            try:
                if hasattr(agent, 'cleanup'):
                    await agent.cleanup()
                logger.info(f"✅ {name} 에이전트 정리 완료")
            except Exception as e:
                logger.error(f"❌ {name} 에이전트 정리 실패: {e}")
        
        logger.info("✅ 오케스트레이터 정리 완료")
