#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
K-ETS Dashboard 웹소켓 API
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from typing import Dict, List, Any
import json
import logging
from datetime import datetime

from app.core.security import verify_token
from app.utils.logger import get_logger
from app.agents.orchestrator import AgentOrchestrator
from app.models.agent_response import ChatMessage, DashboardUpdateMessage, SystemMessage

logger = get_logger(__name__)
router = APIRouter()

class ConnectionManager:
    """웹소켓 연결 관리자"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.orchestrator = AgentOrchestrator()
    
    async def connect(self, websocket: WebSocket):
        """웹소켓 연결"""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"웹소켓 연결 - 총 연결 수: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        """웹소켓 연결 해제"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"웹소켓 연결 해제 - 총 연결 수: {len(self.active_connections)}")
    
    async def send_personal_message(self, message: Dict, websocket: WebSocket):
        """개별 사용자에게 메시지 전송"""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"개별 메시지 전송 실패: {e}")
    
    async def send_dashboard_update(self, data: dict):
        """모든 연결된 클라이언트에게 대시보드 업데이트 전송"""
        message = DashboardUpdateMessage(
            type="dashboard_update", 
            data=data,
            updates=data
        )
        
        for connection in self.active_connections:
            try:
                await connection.send_json(message.dict())
            except Exception as e:
                logger.error(f"대시보드 업데이트 전송 실패: {e}")
    
    async def broadcast_message(self, message: Dict):
        """모든 클라이언트에게 브로드캐스트"""
        disconnected = []
        
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"브로드캐스트 메시지 전송 실패: {e}")
                disconnected.append(connection)
        
        # 연결이 끊어진 웹소켓 제거
        for connection in disconnected:
            self.disconnect(connection)

# 연결 관리자 인스턴스
manager = ConnectionManager()

@router.websocket("/chat")
async def websocket_chat(websocket: WebSocket):
    """AI 채팅 웹소켓 연결"""
    await manager.connect(websocket)
    try:
        while True:
            # 사용자 메시지 수신
            data = await websocket.receive_json()
            
            # ChatMessage 모델로 파싱
            try:
                chat_message = ChatMessage(**data)
            except Exception as e:
                await manager.send_personal_message({
                    "type": "error",
                    "message": f"메시지 형식 오류: {str(e)}"
                }, websocket)
                continue
            
            # 에이전트 오케스트레이터로 처리
            try:
                response = await manager.orchestrator.process_user_input(
                    chat_message.text, 
                    chat_message.context or {}
                )
                
                # 응답 전송
                await manager.send_personal_message({
                    "type": "agent_response",
                    "data": response.dict()
                }, websocket)
                
                # 대시보드 업데이트가 있으면 모든 클라이언트에게 브로드캐스트
                if response.dashboard_updates:
                    await manager.send_dashboard_update(response.dashboard_updates.dict())
                    
            except Exception as e:
                await manager.send_personal_message({
                    "type": "error",
                    "message": f"처리 중 오류가 발생했습니다: {str(e)}"
                }, websocket)
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@router.websocket("/ws/dashboard")  
async def websocket_dashboard(websocket: WebSocket):
    """대시보드 업데이트 웹소켓 연결"""
    await manager.connect(websocket)
    
    try:
        while True:
            # 클라이언트로부터 메시지 수신
            data = await websocket.receive_json()
            
            # 메시지 타입에 따른 처리
            if data.get("type") == "subscribe":
                # 구독 요청 처리
                await manager.send_personal_message({
                    "type": "subscribed",
                    "message": "대시보드 업데이트 구독 완료",
                    "timestamp": datetime.now().isoformat()
                }, websocket)
            
            elif data.get("type") == "ping":
                # 핑 요청에 대한 응답
                await manager.send_personal_message({
                    "type": "pong", 
                    "timestamp": datetime.now().isoformat()
                }, websocket)
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"대시보드 웹소켓 오류: {e}")
        manager.disconnect(websocket)

@router.websocket("/ws/agent")
async def websocket_agent(websocket: WebSocket):
    """AI 에이전트 웹소켓 연결"""
    await manager.connect(websocket, "agent")
    
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("type") == "chat":
                # 채팅 메시지 처리
                response = {
                    "type": "chat_response",
                    "message": f"에이전트 응답: {message.get('content', '')}",
                    "timestamp": datetime.now().isoformat()
                }
                await manager.send_personal_message(json.dumps(response), websocket)
            
            elif message.get("type") == "subscribe_updates":
                # 에이전트 업데이트 구독
                await manager.send_personal_message(
                    json.dumps({
                        "type": "subscribed",
                        "message": "에이전트 업데이트 구독 완료",
                        "timestamp": datetime.now().isoformat()
                    }),
                    websocket
                )
                
    except WebSocketDisconnect:
        manager.disconnect(websocket, "agent")
    except Exception as e:
        logger.error(f"에이전트 웹소켓 오류: {e}")
        manager.disconnect(websocket, "agent")

@router.websocket("/ws/data")
async def websocket_data(websocket: WebSocket):
    """데이터 처리 웹소켓 연결"""
    await manager.connect(websocket, "data")
    
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("type") == "data_processing":
                # 데이터 처리 진행 상황 전송
                progress = {
                    "type": "processing_progress",
                    "file_id": message.get("file_id"),
                    "progress": 50,  # 예시 진행률
                    "status": "processing",
                    "timestamp": datetime.now().isoformat()
                }
                await manager.send_personal_message(json.dumps(progress), websocket)
                
    except WebSocketDisconnect:
        manager.disconnect(websocket, "data")
    except Exception as e:
        logger.error(f"데이터 웹소켓 오류: {e}")
        manager.disconnect(websocket, "data")

@router.websocket("/ws/general")
async def websocket_general(websocket: WebSocket):
    """일반 웹소켓 연결"""
    await manager.connect(websocket, "general")
    
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # 에코 서버 역할
            echo_response = {
                "type": "echo",
                "original_message": message,
                "timestamp": datetime.now().isoformat()
            }
            await manager.send_personal_message(json.dumps(echo_response), websocket)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, "general")
    except Exception as e:
        logger.error(f"일반 웹소켓 오류: {e}")
        manager.disconnect(websocket, "general")

# 웹소켓을 통한 실시간 알림 전송 함수들
async def send_dashboard_update(update_data: Dict[str, Any]):
    """대시보드 업데이트 전송"""
    message = {
        "type": "dashboard_update",
        "data": update_data,
        "timestamp": datetime.now().isoformat()
    }
    await manager.broadcast_to_type(json.dumps(message), "dashboard")

async def send_agent_update(update_data: Dict[str, Any]):
    """에이전트 업데이트 전송"""
    message = {
        "type": "agent_update",
        "data": update_data,
        "timestamp": datetime.now().isoformat()
    }
    await manager.broadcast_to_type(json.dumps(message), "agent")

async def send_data_processing_update(update_data: Dict[str, Any]):
    """데이터 처리 업데이트 전송"""
    message = {
        "type": "data_processing_update",
        "data": update_data,
        "timestamp": datetime.now().isoformat()
    }
    await manager.broadcast_to_type(json.dumps(message), "data")

async def send_system_notification(notification: str, level: str = "info"):
    """시스템 알림 전송"""
    message = {
        "type": "system_notification",
        "notification": notification,
        "level": level,
        "timestamp": datetime.now().isoformat()
    }
    await manager.broadcast_to_all(json.dumps(message))

# 연결 상태 조회
@router.get("/ws/status")
async def get_websocket_status():
    """웹소켓 연결 상태 조회"""
    status = {}
    for client_type, connections in manager.active_connections.items():
        status[client_type] = len(connections)
    
    return {
        "websocket_status": "active",
        "connections": status,
        "total_connections": sum(status.values())
    }
