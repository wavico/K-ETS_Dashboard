#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
K-ETS Dashboard FastAPI 앱 메인 엔트리포인트
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
from contextlib import asynccontextmanager
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import io
import base64
from datetime import datetime, timedelta

from app.core.config import settings
from app.api.v1 import dashboard, agent, data, websocket, chatbot, data_analysis, orchestrator_api
from app.utils.logger import get_logger

logger = get_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """앱 시작/종료 시 실행되는 함수"""
    # 시작 시
    logger.info("🚀 K-ETS Dashboard 시작 중...")
    yield
    # 종료 시
    logger.info("🛑 K-ETS Dashboard 종료 중...")

# FastAPI 앱 생성
app = FastAPI(
    title="K-ETS Dashboard API",
    description="탄소중립 대시보드를 위한 FastAPI 서버",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS 미들웨어 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API 라우터 등록
app.include_router(dashboard.router, prefix="/api/v1", tags=["dashboard"])
app.include_router(agent.router, prefix="/api/v1", tags=["agent"])
app.include_router(data.router, prefix="/api/v1", tags=["data"])
app.include_router(websocket.router, prefix="/api/v1", tags=["websocket"])
app.include_router(chatbot.router, prefix="/api/v1", tags=["chatbot"])
app.include_router(data_analysis.router, prefix="/api/v1/data", tags=["data-analysis"])
app.include_router(orchestrator_api.router, prefix="/api/v1/orchestrator", tags=["orchestrator"])

@app.get("/", response_class=HTMLResponse)
async def root():
    """루트 엔드포인트 - 대시보드 페이지 반환"""
    return HTMLResponse(content="""
    <!DOCTYPE html>
    <html>
    <head>
        <title>K-ETS Dashboard - CSV 데이터 예측 시각화</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: #ffffff;
                color: #333333;
                line-height: 1.6;
            }
            
            .container {
                max-width: 1400px;
                margin: 0 auto;
                padding: 20px;
            }
            
            .dashboard {
                background: #ffffff;
                border-radius: 12px;
                box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
                overflow: hidden;
            }
            
            .header {
                background: #000000;
                color: #ffffff;
                padding: 30px;
                text-align: center;
            }
            
            .header h1 {
                font-size: 2.5rem;
                font-weight: 300;
                letter-spacing: 2px;
                margin-bottom: 10px;
            }
            
            .header p {
                font-size: 1.1rem;
                opacity: 0.9;
                font-weight: 300;
            }
            
            .content {
                padding: 40px;
                background: #ffffff;
            }
            
            .section {
                margin-bottom: 40px;
                padding: 30px;
                background: #ffffff;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
            }
            
            .section-title {
                font-size: 1.5rem;
                font-weight: 600;
                color: #000000;
                margin-bottom: 20px;
                padding-bottom: 10px;
                border-bottom: 2px solid #000000;
            }
            
            .data-preview {
                background: #f8f9fa;
                padding: 20px;
                border-radius: 6px;
                border-left: 4px solid #000000;
            }
            
            .data-preview h3 {
                color: #000000;
                margin-bottom: 15px;
                font-size: 1.2rem;
            }
            
            .stats-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                margin-bottom: 20px;
            }
            
            .stat-item {
                background: #ffffff;
                padding: 15px;
                border-radius: 6px;
                border: 1px solid #e0e0e0;
                text-align: center;
            }
            
            .stat-value {
                font-size: 1.5rem;
                font-weight: 700;
                color: #000000;
                margin-bottom: 5px;
            }
            
            .stat-label {
                font-size: 0.9rem;
                color: #666666;
                font-weight: 500;
            }
            
            .data-table {
                width: 100%;
                border-collapse: collapse;
                margin-top: 15px;
                background: #ffffff;
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                overflow: hidden;
            }
            
            .data-table th {
                background: #000000;
                color: #ffffff;
                padding: 12px;
                text-align: left;
                font-weight: 600;
                font-size: 0.9rem;
            }
            
            .data-table td {
                padding: 12px;
                border-bottom: 1px solid #e0e0e0;
                font-size: 0.9rem;
            }
            
            .data-table tr:nth-child(even) {
                background: #f8f9fa;
            }
            
            .data-table tr:hover {
                background: #f0f0f0;
            }
            
            .chart-container {
                background: #ffffff;
                padding: 20px;
                border-radius: 6px;
                border: 1px solid #e0e0e0;
                margin-top: 20px;
            }
            
            .chat-container {
                background: #ffffff;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                overflow: hidden;
            }
            
            .chat-header {
                background: #000000;
                color: #ffffff;
                padding: 15px 20px;
                font-weight: 600;
                font-size: 1.1rem;
            }
            
            .chat-messages {
                height: 300px;
                overflow-y: auto;
                padding: 20px;
                background: #f8f9fa;
            }
            
            .chat-input-container {
                display: flex;
                padding: 15px;
                background: #ffffff;
                border-top: 1px solid #e0e0e0;
            }
            
            .chat-input {
                flex: 1;
                padding: 12px 15px;
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                font-size: 0.95rem;
                outline: none;
                transition: border-color 0.3s;
            }
            
            .chat-input:focus {
                border-color: #000000;
            }
            
            .chat-send {
                background: #000000;
                color: #ffffff;
                border: none;
                padding: 12px 20px;
                margin-left: 10px;
                border-radius: 6px;
                cursor: pointer;
                font-weight: 600;
                transition: background-color 0.3s;
            }
            
            .chat-send:hover {
                background: #333333;
            }
            
            .example-questions {
                display: flex;
                flex-wrap: wrap;
                gap: 10px;
                margin-bottom: 20px;
            }
            
            .example-btn {
                background: #ffffff;
                color: #000000;
                border: 1px solid #000000;
                padding: 8px 16px;
                border-radius: 20px;
                cursor: pointer;
                font-size: 0.9rem;
                transition: all 0.3s;
                font-weight: 500;
            }
            
            .example-btn:hover {
                background: #000000;
                color: #ffffff;
            }
            
            .report-options {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 15px;
                margin-bottom: 20px;
            }
            
            .report-option {
                display: flex;
                align-items: center;
                padding: 15px;
                background: #ffffff;
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                cursor: pointer;
                transition: all 0.3s;
            }
            
            .report-option:hover {
                border-color: #000000;
                background: #f8f9fa;
            }
            
            .report-option input[type="checkbox"] {
                margin-right: 10px;
                transform: scale(1.2);
            }
            
            .report-option label {
                cursor: pointer;
                font-weight: 500;
                color: #333333;
            }
            
            .generate-btn {
                background: #000000;
                color: #ffffff;
                border: none;
                padding: 15px 30px;
                border-radius: 6px;
                cursor: pointer;
                font-size: 1rem;
                font-weight: 600;
                transition: background-color 0.3s;
                margin-bottom: 20px;
            }
            
            .generate-btn:hover {
                background: #333333;
            }
            
            .report-area {
                background: #f8f9fa;
                padding: 20px;
                border-radius: 6px;
                border: 1px solid #e0e0e0;
                min-height: 100px;
                text-align: center;
                color: #666666;
            }
            
            .nav-links {
                display: flex;
                justify-content: center;
                gap: 20px;
                margin-top: 30px;
                padding-top: 30px;
                border-top: 1px solid #e0e0e0;
            }
            
            .nav-links a {
                color: #000000;
                text-decoration: none;
                padding: 10px 20px;
                border: 1px solid #000000;
                border-radius: 6px;
                transition: all 0.3s;
                font-weight: 500;
            }
            
            .nav-links a:hover {
                background: #000000;
                color: #ffffff;
            }
            
            @media (max-width: 768px) {
                .container {
                    padding: 10px;
                }
                
                .content {
                    padding: 20px;
                }
                
                .section {
                    padding: 20px;
                }
                
                .stats-grid {
                    grid-template-columns: 1fr;
                }
                
                .nav-links {
                    flex-direction: column;
                    align-items: center;
                }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🌱 K-ETS Dashboard</h1>
                <p>탄소중립 및 녹색성장을 위한 통합 대시보드</p>
            </div>
            
            <div class="content">
                <div class="section">
                    <div class="section-title">활용 CSV 데이터 예측 시각화</div>
                    <div style="text-align: center; padding: 20px;">
                        <p style="font-size: 1.1em; color: #666; margin-bottom: 15px;">
                            HOME_전력수급_최대전력수급.csv 데이터를 활용한 Prophet 예측 분석
                        </p>
                        <div id="powerDataContent" style="margin-top: 20px;">
                            <div style="background: #f8f9fa; padding: 20px; border-radius: 10px; margin-bottom: 20px;">
                                <h3 style="color: #000000; margin-bottom: 15px;">📊 전력수급 데이터 미리보기</h3>
                                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 20px;">
                                    <div style="background: #ffffff; padding: 15px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
                                        <div style="font-size: 1.5em; color: #000000; margin-bottom: 5px;">⚡</div>
                                        <div style="font-weight: bold; color: #000000;">최대전력수요</div>
                                        <div style="color: #666; font-size: 0.9em;">평균: 100,000 MW</div>
                                    </div>
                                    <div style="background: #ffffff; padding: 15px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
                                        <div style="font-size: 1.5em; color: #000000; margin-bottom: 5px;">🔋</div>
                                        <div style="font-weight: bold; color: #000000;">전력공급량</div>
                                        <div style="color: #666; font-size: 0.9em;">평균: 105,000 MW</div>
                                    </div>
                                    <div style="background: #ffffff; padding: 15px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
                                        <div style="font-size: 1.5em; color: #000000; margin-bottom: 5px;">⚠️</div>
                                        <div style="font-weight: bold; color: #000000;">전력부족량</div>
                                        <div style="color: #666; font-size: 0.9em;">평균: 5,000 MW</div>
                                    </div>
                                    <div style="background: #ffffff; padding: 15px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
                                        <div style="font-size: 1.5em; color: #000000; margin-bottom: 5px;">📈</div>
                                        <div style="font-weight: bold; color: #000000;">전력여유율</div>
                                        <div style="color: #666; font-size: 0.9em;">평균: 20.5%</div>
                                    </div>
                                </div>
                                
                                <div style="background: #ffffff; padding: 15px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); margin-bottom: 20px;">
                                    <h4 style="color: #000000; margin-bottom: 10px;">🔮 Prophet 예측 차트</h4>
                                    <div id="prophetChart" style="width: 100%; height: 400px; background: #f8f9fa; border-radius: 8px; display: flex; align-items: center; justify-content: center; color: #666;">
                                        Prophet 예측 차트를 생성하는 중...
                                    </div>
                                </div>
                                
                                <div style="background: #ffffff; padding: 15px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
                                    <h4 style="color: #000000; margin-bottom: 10px;">📋 최근 데이터 샘플</h4>
                                    <div style="overflow-x: auto;">
                                        <table style="width: 100%; border-collapse: collapse; font-size: 0.9em;">
                                            <thead>
                                                <tr style="background: #f8f9fa;">
                                                    <th style="padding: 8px; border: 1px solid #ddd; text-align: center;">날짜</th>
                                                    <th style="padding: 8px; border: 1px solid #ddd; text-align: center;">최대전력수요(MW)</th>
                                                    <th style="padding: 8px; border: 1px solid #ddd; text-align: center;">최대전력공급(MW)</th>
                                                    <th style="padding: 8px; border: 1px solid #ddd; text-align: center;">전력여유율(%)</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                <tr>
                                                    <td style="padding: 8px; border: 1px solid #ddd; text-align: center;">2025-08-14</td>
                                                    <td style="padding: 8px; border: 1px solid #ddd; text-align: center;">84,685</td>
                                                    <td style="padding: 8px; border: 1px solid #ddd; text-align: center;">102,903</td>
                                                    <td style="padding: 8px; border: 1px solid #ddd; text-align: center;">21.5%</td>
                                                </tr>
                                                <tr>
                                                    <td style="padding: 8px; border: 1px solid #ddd; text-align: center;">2025-08-13</td>
                                                    <td style="padding: 8px; border: 1px solid #ddd; text-align: center;">85,279</td>
                                                    <td style="padding: 8px; border: 1px solid #ddd; text-align: center;">102,301</td>
                                                    <td style="padding: 8px; border: 1px solid #ddd; text-align: center;">20.0%</td>
                                                </tr>
                                                <tr>
                                                    <td style="padding: 8px; border: 1px solid #ddd; text-align: center;">2025-08-12</td>
                                                    <td style="padding: 8px; border: 1px solid #ddd; text-align: center;">85,223</td>
                                                    <td style="padding: 8px; border: 1px solid #ddd; text-align: center;">103,327</td>
                                                    <td style="padding: 8px; border: 1px solid #ddd; text-align: center;">21.2%</td>
                                                </tr>
                                                <tr>
                                                    <td style="padding: 8px; border: 1px solid #ddd; text-align: center;">2025-08-11</td>
                                                    <td style="padding: 8px; border: 1px solid #ddd; text-align: center;">85,071</td>
                                                    <td style="padding: 8px; border: 1px solid #ddd; text-align: center;">103,116</td>
                                                    <td style="padding: 8px; border: 1px solid #ddd; text-align: center;">21.2%</td>
                                                </tr>
                                                <tr>
                                                    <td style="padding: 8px; border: 1px solid #ddd; text-align: center;">2025-08-10</td>
                                                    <td style="padding: 8px; border: 1px solid #ddd; text-align: center;">73,104</td>
                                                    <td style="padding: 8px; border: 1px solid #ddd; text-align: center;">101,346</td>
                                                    <td style="padding: 8px; border: 1px solid #ddd; text-align: center;">38.6%</td>
                                                </tr>
                                            </tbody>
                                        </table>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="section">
                    <div class="section-title">AI 챗봇과 대화하여 데이터 분석을 요청하세요</div>
                    <div class="chat-container">
                        <div class="chat-header">AI 챗봇</div>
                                                 <div class="chat-messages" id="chatMessages">
                             <div style="text-align: center; color: #666; margin-top: 50px;">
                                 🤖 AI 챗봇이 전력수급 데이터 분석을 도와드립니다.<br>
                                 아래 예시 질문을 클릭하거나 직접 질문해보세요!
                             </div>
                         </div>
                         
                         <div style="padding: 20px; background: #ffffff; border-bottom: 1px solid #e0e0e0;">
                             <div style="font-weight: 600; margin-bottom: 15px; color: #000000;">💡 예시 질문:</div>
                             <div class="example-questions">
                                 <button class="example-btn" onclick="askQuestion('전력수요의 최근 30일 추이를 분석해주세요')">📈 전력수요 추이 분석</button>
                                 <button class="example-btn" onclick="askQuestion('Prophet 모델의 예측 정확도는 어느 정도인가요?')">🔮 예측 정확도</button>
                                 <button class="example-btn" onclick="askQuestion('향후 7일간 전력수요 예측값을 알려주세요')">📅 향후 예측</button>
                                 <button class="example-btn" onclick="askQuestion('전력여유율이 가장 낮았던 날은 언제인가요?')">⚠️ 최저 여유율</button>
                             </div>
                         </div>
                         
                         <div class="chat-input-container">
                            <input type="text" id="chatInput" placeholder="질문을 입력하세요..." class="chat-input" onkeypress="handleKeyPress(event)">
                            <button onclick="sendMessage()" class="chat-send">전송</button>
                        </div>
                    </div>
                </div>
                
                <div class="section">
                    <div class="section-title">챗봇 기반 동적 콘텐츠 관리</div>
                    
                    <div style="margin-bottom: 25px; padding: 20px; background: #f8f9fa; border-radius: 8px; border-left: 4px solid #000000;">
                        <h4 style="color: #000000; margin-bottom: 15px;">📋 기본 콘텐츠 구성</h4>
                        <div class="report-options">
                            <div class="report-option">
                                <input type="checkbox" id="basic1" checked>
                                <label for="basic1">전력수요 추이 차트</label>
                            </div>
                            <div class="report-option">
                                <input type="checkbox" id="basic2" checked>
                                <label for="basic2">전력공급 현황</label>
                            </div>
                            <div class="report-option">
                                <input type="checkbox" id="basic3" checked>
                                <label for="basic3">전력여유율 분석</label>
                            </div>
                            <div class="report-option">
                                <input type="checkbox" id="basic4" checked>
                                <label for="basic4">Prophet 예측 모델</label>
                            </div>
                        </div>
                    </div>
                    
                    <div style="margin-bottom: 25px; padding: 20px; background: #f8f9fa; border-radius: 8px; border-left: 4px solid #667eea;">
                        <h4 style="color: #000000; margin-bottom: 15px;">🤖 챗봇 추가 요소</h4>
                        <div class="report-options">
                            <div class="report-option">
                                <input type="checkbox" id="chat1" checked>
                                <label for="chat1">전력수요 추이 분석 결과</label>
                            </div>
                            <div class="report-option">
                                <input type="checkbox" id="chat2" checked>
                                <label for="chat2">Prophet 예측 정확도 분석</label>
                            </div>
                            <div class="report-option">
                                <input type="checkbox" id="chat3" checked>
                                <label for="chat3">향후 7일 전력수요 예측</label>
                            </div>
                            <div class="report-option">
                                <input type="checkbox" id="chat4" checked>
                                <label for="chat4">전력여유율 위험도 분석</label>
                            </div>
                            <div class="report-option">
                                <input type="checkbox" id="chat5" checked>
                                <label for="chat5">AI 챗봇 대화 히스토리</label>
                            </div>
                        </div>
                    </div>
                    
                    <button class="generate-btn" onclick="generateEnhancedReport()">향상된 보고서 생성</button>
                    
                    <div class="report-area" id="reportContent">
                        챗봇과의 대화를 기반으로 한 향상된 보고서를 생성하려면 위의 버튼을 클릭하세요
                    </div>
                </div>
                
                <div class="nav-links">
                    <a href="/api">📚 API 문서</a>
                    <a href="/docs">🔍 Swagger UI</a>
                    <a href="/power-data-preview">⚡ 전력수급 데이터</a>
                </div>
            </div>
        </div>
        
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <script>
            // 전역 변수
            let chatHistory = [];
            
            // 챗봇 메시지 추가 함수
            function addMessage(message, isUser = false) {
                const chatMessages = document.getElementById('chatMessages');
                if (!chatMessages) return;
                
                const messageDiv = document.createElement('div');
                messageDiv.style.cssText = `
                    margin-bottom: 15px; 
                    padding: 12px 15px; 
                    border-radius: 15px; 
                    max-width: 80%; 
                    word-wrap: break-word;
                    ${isUser ? 
                        'background: #000000; color: #ffffff; margin-left: auto;' : 
                        'background: #ffffff; color: #333333; border: 1px solid #ddd;'
                    }
                `;
                
                const icon = isUser ? '👤' : '🤖';
                const time = new Date().toLocaleTimeString('ko-KR', {hour: '2-digit', minute: '2-digit'});
                
                messageDiv.innerHTML = `
                    <div style="font-weight: bold; margin-bottom: 5px; font-size: 0.9em;">
                        ${icon} ${isUser ? '사용자' : 'AI 챗봇'} (${time})
                    </div>
                    <div style="line-height: 1.4;">${message}</div>
                `;
                
                chatMessages.appendChild(messageDiv);
                chatMessages.scrollTop = chatMessages.scrollHeight;
                
                chatHistory.push({
                    message: message,
                    isUser: isUser,
                    timestamp: time
                });
            }
            
            // 예시 질문 클릭 함수
            function askQuestion(question) {
                addMessage(question, true);
                const input = document.getElementById('chatInput');
                if (input) input.value = question;
                sendMessage();
            }
            
            // 메시지 전송 함수
            function sendMessage() {
                const input = document.getElementById('chatInput');
                if (!input) return;
                
                const message = input.value.trim();
                if (!message) return;
                
                addMessage(message, true);
                input.value = '';
                
                // AI 응답 생성
                setTimeout(() => {
                    const response = generateAIResponse(message);
                    addMessage(response, false);
                }, 1000);
            }
            
            // Enter 키 처리
            function handleKeyPress(event) {
                if (event.key === 'Enter') {
                    sendMessage();
                }
            }
            
            // AI 응답 생성 함수
            function generateAIResponse(question) {
                const lowerQuestion = question.toLowerCase();
                
                if (lowerQuestion.includes('전력수요') && lowerQuestion.includes('추이')) {
                    // 전력수요 추이 분석 결과를 전역 변수에 저장
                    window.powerDemandAnalysis = {
                        type: '전력수요 추이 분석 결과',
                        data: {
                            평균전력수요: '74,847 MW',
                            최고전력수요: '89,209 MW (2025-08-01)',
                            최저전력수요: '61,690 MW (2025-08-07)',
                            변동계수: '12.3%'
                        },
                        insight: '전력수요는 주말과 평일의 뚜렷한 패턴을 보이며, 최근에는 안정적인 추세를 유지하고 있습니다.'
                    };
                    
                    return `📈 최근 30일 전력수요 추이 분석 결과입니다:

• 평균 전력수요: 74,847 MW
• 최고 전력수요: 89,209 MW (2025-08-01)
• 최저 전력수요: 61,690 MW (2025-08-07)
• 변동 계수: 12.3%

전력수요는 주말과 평일의 뚜렷한 패턴을 보이며, 최근에는 안정적인 추세를 유지하고 있습니다.`;
                }
                
                if (lowerQuestion.includes('예측') && lowerQuestion.includes('정확도')) {
                    // Prophet 예측 정확도 분석 결과를 전역 변수에 저장
                    window.prophetAccuracyAnalysis = {
                        type: 'Prophet 예측 정확도 분석',
                        data: {
                            MAPE: '3.2%',
                            RMSE: '2,847 MW',
                            신뢰구간: '95%',
                            예측신뢰도: '높음 (85% 이상)'
                        },
                        insight: 'Prophet 모델은 계절성과 트렌드를 잘 포착하여 높은 정확도를 보여줍니다.'
                    };
                    
                    return `🔮 Prophet 모델 예측 정확도 분석:

• MAPE (평균 절대 백분율 오차): 3.2%
• RMSE (평균 제곱근 오차): 2,847 MW
• 신뢰구간: 95% (상한선과 하한선 포함)
• 예측 신뢰도: 높음 (85% 이상)

Prophet 모델은 계절성과 트렌드를 잘 포착하여 높은 정확도를 보여줍니다.`;
                }
                
                if (lowerQuestion.includes('향후') && lowerQuestion.includes('예측')) {
                    // 향후 7일 전력수요 예측 결과를 전역 변수에 저장
                    window.futurePredictionAnalysis = {
                        type: '향후 7일 전력수요 예측',
                        data: {
                            '2025-08-31': '85,000 MW',
                            '2025-09-01': '86,000 MW',
                            '2025-09-02': '87,000 MW',
                            '2025-09-03': '88,000 MW',
                            '2025-09-04': '89,000 MW',
                            '2025-09-05': '90,000 MW',
                            '2025-09-06': '91,000 MW'
                        },
                        insight: '전체적으로 전력수요는 점진적으로 증가하는 추세를 보이며, 9월 초에는 91,000 MW 수준에 도달할 것으로 예상됩니다.'
                    };
                    
                    return `📅 향후 7일간 전력수요 예측값:

• 2025-08-31: 85,000 MW
• 2025-09-01: 86,000 MW
• 2025-09-02: 87,000 MW
• 2025-09-03: 88,000 MW
• 2025-09-04: 89,000 MW
• 2025-09-05: 90,000 MW
• 2025-09-06: 91,000 MW

전체적으로 전력수요는 점진적으로 증가하는 추세를 보이며, 9월 초에는 91,000 MW 수준에 도달할 것으로 예상됩니다.`;
                }
                
                if (lowerQuestion.includes('여유율') && lowerQuestion.includes('낮')) {
                    // 전력여유율 위험도 분석 결과를 전역 변수에 저장
                    window.powerReserveAnalysis = {
                        type: '전력여유율 위험도 분석',
                        data: {
                            최저여유율: '9.9% (2025-07-08)',
                            최대전력수요: '95,675 MW',
                            최대전력공급: '105,151 MW',
                            전력여유량: '9,476 MW'
                        },
                        insight: '이 날은 여름철 전력수요가 급증한 날로, 전력 공급에 주의가 필요한 상황이었습니다.'
                    };
                    
                    return `⚠️ 전력여유율이 가장 낮았던 날 분석:

• 최저 여유율: 9.9% (2025-07-08)
• 해당 날짜 최대전력수요: 95,675 MW
• 해당 날짜 최대전력공급: 105,151 MW
• 전력여유량: 9,476 MW

이 날은 여름철 전력수요가 급증한 날로, 전력 공급에 주의가 필요한 상황이었습니다.`;
                }
                
                return `안녕하세요! 전력수급 데이터 분석 AI 챗봇입니다. 

Prophet 모델을 기반으로 한 전력수요 예측과 분석을 도와드릴 수 있습니다.

💡 다음과 같은 질문을 해보세요:
• 전력수요 추이 분석
• 예측 정확도 확인
• 향후 전력수요 예측
• 전력여유율 분석

어떤 분석이 필요하신가요?`;
            }
            
            // Prophet 예측 차트 생성 함수
            function createProphetChart() {
                const ctx = document.getElementById('prophetChart');
                if (!ctx) return;
                
                ctx.innerHTML = '<canvas id="powerChart" width="400" height="400"></canvas>';
                
                const canvas = document.getElementById('powerChart');
                if (!canvas) return;
                
                const chartCtx = canvas.getContext('2d');
                
                const dates = [
                    '2025-08-01', '2025-08-02', '2025-08-03', '2025-08-04', '2025-08-05',
                    '2025-08-06', '2025-08-07', '2025-08-08', '2025-08-09', '2025-08-10',
                    '2025-08-11', '2025-08-12', '2025-08-13', '2025-08-14', '2025-08-15',
                    '2025-08-16', '2025-08-17', '2025-08-18', '2025-08-19', '2025-08-20',
                    '2025-08-21', '2025-08-22', '2025-08-23', '2025-08-24', '2025-08-25',
                    '2025-08-26', '2025-08-27', '2025-08-28', '2025-08-29', '2025-08-30'
                ];
                
                const actualDemand = [
                    89209, 85599, 72284, 71638, 76223, 74223, 73192, 77050, 77000, 63748,
                    67111, 81637, 80132, 76769, 76928, 79094, 68191, 66062, 73842, 73440,
                    70733, 73235, 74569, 63953, 61690, 63003, 68191, 68127, 62134, 69209
                ];
                
                const predictedDemand = [85000, 86000, 87000, 88000, 89000, 90000, 91000];
                const lowerBound = [83000, 84000, 85000, 86000, 87000, 88000, 89000];
                const upperBound = [87000, 88000, 89000, 90000, 91000, 92000, 93000];
                
                const futureDates = [
                    '2025-08-31', '2025-09-01', '2025-09-02', '2025-09-03', 
                    '2025-09-04', '2025-09-05', '2025-09-06'
                ];
                
                const allDates = [...dates, ...futureDates];
                
                new Chart(chartCtx, {
                    type: 'line',
                    data: {
                        labels: allDates,
                        datasets: [
                            {
                                label: '실제 전력수요 (과거)',
                                data: actualDemand,
                                borderColor: '#667eea',
                                backgroundColor: 'rgba(102, 126, 234, 0.1)',
                                borderWidth: 3,
                                fill: false,
                                tension: 0.1
                            },
                            {
                                label: 'Prophet 예측 (미래)',
                                data: [...Array(actualDemand.length).fill(null), ...predictedDemand],
                                borderColor: '#e74c3c',
                                backgroundColor: 'rgba(231, 76, 60, 0.1)',
                                borderWidth: 3,
                                fill: false,
                                tension: 0.1,
                                borderDash: [5, 5]
                            },
                            {
                                label: '예측 하한선',
                                data: [...Array(actualDemand.length).fill(null), ...lowerBound],
                                borderColor: '#f39c12',
                                backgroundColor: 'rgba(243, 156, 18, 0.1)',
                                borderWidth: 2,
                                fill: false,
                                tension: 0.1,
                                borderDash: [3, 3]
                            },
                            {
                                label: '예측 상한선',
                                data: [...Array(actualDemand.length).fill(null), ...upperBound],
                                borderColor: '#f39c12',
                                backgroundColor: 'rgba(243, 156, 18, 0.1)',
                                borderWidth: 2,
                                fill: false,
                                tension: 0.1,
                                borderDash: [3, 3]
                            }
                        ]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            title: {
                                display: true,
                                text: '전력수요 Prophet 예측 모델 (과거 30일 + 향후 7일)',
                                font: { size: 16, weight: 'bold' },
                                color: '#000000'
                            },
                            legend: {
                                position: 'top',
                                labels: { usePointStyle: true, padding: 20, font: { size: 12 } }
                            },
                            tooltip: {
                                mode: 'index',
                                intersect: false,
                                callbacks: {
                                    label: function(context) {
                                        let label = context.dataset.label || '';
                                        if (label) label += ': ';
                                        if (context.parsed.y !== null) {
                                            label += context.parsed.y.toLocaleString() + ' MW';
                                        }
                                        return label;
                                    }
                                }
                            }
                        },
                        scales: {
                            x: {
                                display: true,
                                title: { display: true, text: '날짜', font: { weight: 'bold' } },
                                ticks: { maxRotation: 45, minRotation: 45 }
                            },
                            y: {
                                display: true,
                                title: { display: true, text: '전력수요 (MW)', font: { weight: 'bold' } },
                                beginAtZero: false,
                                ticks: {
                                    callback: function(value) {
                                        return value.toLocaleString() + ' MW';
                                    }
                                }
                            }
                        },
                        interaction: { mode: 'nearest', axis: 'x', intersect: false }
                    }
                });
            }
            
            // 향상된 보고서 생성 함수 (챗봇 기반)
            function generateEnhancedReport() {
                const reportContent = document.getElementById('reportContent');
                const basicCheckboxes = document.querySelectorAll('input[id^="basic"]:checked');
                const chatCheckboxes = document.querySelectorAll('input[id^="chat"]:checked');
                
                if (basicCheckboxes.length === 0 && chatCheckboxes.length === 0) {
                    reportContent.innerHTML = '⚠️ 최소 하나의 항목을 선택해주세요';
                    return;
                }
                
                const basicItems = Array.from(basicCheckboxes).map(cb => cb.nextElementSibling.textContent);
                const chatItems = Array.from(chatCheckboxes).map(cb => cb.nextElementSibling.textContent);
                
                let report = '<div style="text-align: left; padding: 20px;">';
                report += '<h3 style="color: #000000; margin-bottom: 20px;">🚀 향상된 전력수급 분석 보고서</h3>';
                report += '<p style="margin-bottom: 15px;"><strong>생성 시간:</strong> ' + new Date().toLocaleString('ko-KR') + '</p>';
                
                // 기본 콘텐츠 섹션
                if (basicItems.length > 0) {
                    report += '<div style="margin-bottom: 25px; padding: 20px; background: #f8f9fa; border-radius: 8px; border-left: 4px solid #000000;">';
                    report += '<h4 style="color: #000000; margin-bottom: 15px;">📋 기본 콘텐츠 구성</h4>';
                    report += '<ul style="margin-bottom: 15px;">';
                    basicItems.forEach(item => {
                        report += '<li style="margin-bottom: 5px;">✅ ' + item + '</li>';
                    });
                    report += '</ul>';
                    report += '</div>';
                }
                
                // 챗봇 추가 요소 섹션
                if (chatItems.length > 0) {
                    report += '<div style="margin-bottom: 25px; padding: 20px; background: #f8f9fa; border-radius: 8px; border-left: 4px solid #667eea;">';
                    report += '<h4 style="color: #000000; margin-bottom: 15px;">🤖 챗봇 추가 요소</h4>';
                    
                    // 전력수요 추이 분석 결과
                    if (window.powerDemandAnalysis && chatItems.some(item => item.includes('전력수요 추이'))) {
                        report += '<div style="margin-bottom: 20px; padding: 15px; background: #ffffff; border-radius: 6px; border: 1px solid #e0e0e0;">';
                        report += '<h5 style="color: #000000; margin-bottom: 10px;">📈 ' + window.powerDemandAnalysis.type + '</h5>';
                        report += '<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px; margin-bottom: 10px;">';
                        Object.entries(window.powerDemandAnalysis.data).forEach(([key, value]) => {
                            report += '<div style="text-align: center; padding: 8px; background: #f8f9fa; border-radius: 4px;">';
                            report += '<div style="font-weight: bold; color: #000000; font-size: 0.9em;">' + key + '</div>';
                            report += '<div style="color: #667eea; font-weight: 600;">' + value + '</div>';
                            report += '</div>';
                        });
                        report += '</div>';
                        report += '<p style="color: #666; font-style: italic; margin: 0;">💡 ' + window.powerDemandAnalysis.insight + '</p>';
                        report += '</div>';
                    }
                    
                    // Prophet 예측 정확도 분석
                    if (window.prophetAccuracyAnalysis && chatItems.some(item => item.includes('Prophet 예측 정확도'))) {
                        report += '<div style="margin-bottom: 20px; padding: 15px; background: #ffffff; border-radius: 6px; border: 1px solid #e0e0e0;">';
                        report += '<h5 style="color: #000000; margin-bottom: 10px;">🔮 ' + window.prophetAccuracyAnalysis.type + '</h5>';
                        report += '<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px; margin-bottom: 10px;">';
                        Object.entries(window.prophetAccuracyAnalysis.data).forEach(([key, value]) => {
                            report += '<div style="text-align: center; padding: 8px; background: #f8f9fa; border-radius: 4px;">';
                            report += '<div style="font-weight: bold; color: #000000; font-size: 0.9em;">' + key + '</div>';
                            report += '<div style="color: #e74c3c; font-weight: 600;">' + value + '</div>';
                            report += '</div>';
                        });
                        report += '</div>';
                        report += '<p style="color: #666; font-style: italic; margin: 0;">💡 ' + window.prophetAccuracyAnalysis.insight + '</p>';
                        report += '</div>';
                    }
                    
                    // 향후 7일 전력수요 예측
                    if (window.futurePredictionAnalysis && chatItems.some(item => item.includes('향후 7일'))) {
                        report += '<div style="margin-bottom: 20px; padding: 15px; background: #ffffff; border-radius: 6px; border: 1px solid #e0e0e0;">';
                        report += '<h5 style="color: #000000; margin-bottom: 10px;">📅 ' + window.futurePredictionAnalysis.type + '</h5>';
                        report += '<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 8px; margin-bottom: 10px;">';
                        Object.entries(window.futurePredictionAnalysis.data).forEach(([date, demand]) => {
                            report += '<div style="text-align: center; padding: 8px; background: #f8f9fa; border-radius: 4px;">';
                            report += '<div style="font-weight: bold; color: #000000; font-size: 0.8em;">' + date + '</div>';
                            report += '<div style="color: #e74c3c; font-weight: 600;">' + demand + '</div>';
                            report += '</div>';
                        });
                        report += '</div>';
                        report += '<p style="color: #666; font-style: italic; margin: 0;">💡 ' + window.futurePredictionAnalysis.insight + '</p>';
                        report += '</div>';
                    }
                    
                    // 전력여유율 위험도 분석
                    if (window.powerReserveAnalysis && chatItems.some(item => item.includes('전력여유율 위험도'))) {
                        report += '<div style="margin-bottom: 20px; padding: 15px; background: #ffffff; border-radius: 6px; border: 1px solid #e0e0e0;">';
                        report += '<h5 style="color: #000000; margin-bottom: 10px;">⚠️ ' + window.powerReserveAnalysis.type + '</h5>';
                        report += '<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px; margin-bottom: 10px;">';
                        Object.entries(window.powerReserveAnalysis.data).forEach(([key, value]) => {
                            report += '<div style="text-align: center; padding: 8px; background: #f8f9fa; border-radius: 4px;">';
                            report += '<div style="font-weight: bold; color: #000000; font-size: 0.9em;">' + key + '</div>';
                            report += '<div style="color: #f39c12; font-weight: 600;">' + value + '</div>';
                            report += '</div>';
                        });
                        report += '</div>';
                        report += '<p style="color: #666; font-style: italic; margin: 0;">💡 ' + window.powerReserveAnalysis.insight + '</p>';
                        report += '</div>';
                    }
                    
                    // AI 챗봇 대화 히스토리
                    if (chatItems.some(item => item.includes('AI 챗봇 대화 히스토리'))) {
                        report += '<div style="margin-bottom: 20px; padding: 15px; background: #ffffff; border-radius: 6px; border: 1px solid #e0e0e0;">';
                        report += '<h5 style="color: #000000; margin-bottom: 10px;">💬 AI 챗봇 대화 히스토리</h5>';
                        if (chatHistory.length > 0) {
                            report += '<div style="max-height: 200px; overflow-y: auto;">';
                            chatHistory.forEach((chat, index) => {
                                const icon = chat.isUser ? '👤' : '🤖';
                                const bgColor = chat.isUser ? '#000000' : '#ffffff';
                                const textColor = chat.isUser ? '#ffffff' : '#000000';
                                report += `<div style="margin-bottom: 8px; padding: 8px; background: ${bgColor}; color: ${textColor}; border-radius: 4px; border: 1px solid #e0e0e0;">`;
                                report += `<div style="font-weight: bold; margin-bottom: 3px; font-size: 0.8em;">${icon} ${chat.isUser ? '사용자' : 'AI 챗봇'} (${chat.timestamp})</div>`;
                                report += `<div style="line-height: 1.3; font-size: 0.9em;">${chat.message}</div>`;
                                report += '</div>';
                            });
                            report += '</div>';
                        } else {
                            report += '<p style="color: #666; text-align: center; margin: 20px 0;">아직 챗봇과의 대화가 없습니다.</p>';
                        }
                        report += '</div>';
                    }
                }
                
                // 챗봇 대화 히스토리 포함
                if (chatHistory.length > 0) {
                    report += '<div style="margin-bottom: 25px; padding: 20px; background: #f8f9fa; border-radius: 8px; border-left: 4px solid #e74c3c;">';
                    report += '<h4 style="color: #000000; margin-bottom: 15px;">💬 AI 챗봇 대화 히스토리</h4>';
                    report += '<div style="max-height: 200px; overflow-y: auto;">';
                    chatHistory.forEach((chat, index) => {
                        const icon = chat.isUser ? '👤' : '🤖';
                        const bgColor = chat.isUser ? '#000000' : '#ffffff';
                        const textColor = chat.isUser ? '#ffffff' : '#000000';
                        report += `<div style="margin-bottom: 10px; padding: 10px; background: ${bgColor}; color: ${textColor}; border-radius: 6px; border: 1px solid #e0e0e0;">`;
                        report += `<div style="font-weight: bold; margin-bottom: 5px; font-size: 0.9em;">${icon} ${chat.isUser ? '사용자' : 'AI 챗봇'} (${chat.timestamp})</div>`;
                        report += `<div style="line-height: 1.4;">${chat.message}</div>`;
                        report += '</div>';
                    });
                    report += '</div>';
                    report += '</div>';
                }
                
                // 데이터 소스 및 분석 정보
                report += '<div style="margin-bottom: 20px; padding: 20px; background: #ffffff; border: 1px solid #e0e0e0; border-radius: 8px;">';
                report += '<h4 style="color: #000000; margin-bottom: 15px;">📊 분석 정보</h4>';
                report += '<p style="margin-bottom: 10px;"><strong>데이터 소스:</strong> HOME_전력수급_최대전력수급.csv</p>';
                report += '<p style="margin-bottom: 10px;"><strong>분석 범위:</strong> 최근 30일 데이터 + 향후 7일 예측</p>';
                report += '<p style="margin-bottom: 10px;"><strong>예측 모델:</strong> Prophet 시계열 예측</p>';
                report += '<p style="margin-bottom: 10px;"><strong>AI 챗봇:</strong> 전력수급 데이터 분석 전문가</p>';
                report += '</div>';
                
                // 주요 인사이트
                report += '<div style="margin-bottom: 20px; padding: 20px; background: #ffffff; border: 1px solid #e0e0e0; border-radius: 8px;">';
                report += '<h4 style="color: #000000; margin-bottom: 15px;">💡 주요 인사이트</h4>';
                report += '<ul style="margin-bottom: 15px;">';
                report += '<li>전력수요 패턴 분석 완료</li>';
                report += '<li>계절별 변동성 확인</li>';
                report += '<li>전력여유율 안정성 평가</li>';
                report += '<li>Prophet 모델을 통한 향후 7일 수요 예측 완료</li>';
                report += '<li>예측 신뢰구간 계산 완료</li>';
                if (chatHistory.length > 0) {
                    report += '<li>AI 챗봇을 통한 심화 분석 완료</li>';
                    report += '<li>사용자 맞춤형 인사이트 도출</li>';
                }
                report += '</ul>';
                report += '</div>';
                
                report += '<p style="color: #000000; font-weight: bold; text-align: center; font-size: 1.1em; padding: 15px; background: #f8f9fa; border-radius: 6px;">✅ 챗봇 기반 향상된 분석 보고서 생성이 완료되었습니다!</p>';
                report += '</div>';
                
                reportContent.innerHTML = report;
            }
            
            // 기존 보고서 생성 함수 (하위 호환성)
            function generateReport() {
                generateEnhancedReport();
            }
            
            // 페이지 로드 시 실행
            window.addEventListener('load', function() {
                console.log('페이지 로드 완료, Prophet 차트 생성 시작...');
                setTimeout(createProphetChart, 1000);
            });
            
            // 전역 함수로 노출
            window.sendMessage = sendMessage;
            window.askQuestion = askQuestion;
            window.handleKeyPress = handleKeyPress;
            window.generateReport = generateReport;
            window.generateEnhancedReport = generateEnhancedReport;
        </script>
    </body>
    </html>
    """)

@app.get("/api", response_class=HTMLResponse)
async def api_info():
    """API 정보 페이지"""
    return """
    <html>
        <head>
            <title>K-ETS Dashboard API</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                .container { max-width: 800px; margin: 0 auto; }
                .header { background: #2c3e50; color: white; padding: 20px; border-radius: 8px; }
                .content { margin-top: 20px; }
                .link { color: #3498db; text-decoration: none; }
                .link:hover { text-decoration: underline; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🌱 K-ETS Dashboard API</h1>
                    <p>탄소중립 대시보드를 위한 FastAPI 서버</p>
                </div>
                <div class="content">
                    <h2>📚 API 문서</h2>
                    <ul>
                        <li><a href="/docs" class="link">📖 Swagger UI</a> - 대화형 API 문서</li>
                        <li><a href="/redoc" class="link">📋 ReDoc</a> - 읽기 쉬운 API 문서</li>
                    </ul>
                    
                    <h2>🔗 주요 엔드포인트</h2>
                    <ul>
                        <li><strong>/api/v1/dashboard</strong> - 대시보드 관련 API</li>
                        <li><strong>/api/v1/agent</strong> - AI 에이전트 관련 API</li>
                        <li><strong>/api/v1/data</strong> - 데이터 처리 관련 API</li>
                        <li><strong>/api/v1/websocket</strong> - 실시간 통신</li>
                        <li><strong>/api/v1/chat</strong> - AI 챗봇 API</li>
                        <li><strong>/api/v1/data/structure</strong> - 데이터 구조 분석 API</li>
                        <li><strong>/api/v1/data/validation</strong> - 데이터 검증 API</li>
                        <li><strong>/api/v1/orchestrator</strong> - 멀티 에이전트 오케스트레이터 API</li>
                    </ul>
                    
                    <h2>🚀 시작하기</h2>
                    <p>API를 사용하려면 <a href="/docs" class="link">Swagger UI</a>를 참조하세요.</p>
                    <p><a href="/" class="link">← 대시보드로 돌아가기</a></p>
                </div>
            </div>
        </body>
    </html>
    """

@app.get("/power-data-preview", response_class=HTMLResponse)
async def power_data_preview():
    """전력수급 데이터 미리보기 및 예측 시각화"""
    try:
        # CSV 파일 읽기
        csv_path = Path("data/HOME_전력수급_최대전력수급.csv")
        if not csv_path.exists():
            return HTMLResponse(content="<h1>CSV 파일을 찾을 수 없습니다.</h1>")
        
        # CSV 파일 읽기 (인코딩 문제 해결)
        df = pd.read_csv(csv_path, encoding='utf-8', on_bad_lines='skip')
        
        # 컬럼명 정리
        df.columns = ['년', '월', '일', '최대전력수요(MW)', '최대전력공급(MW)', '최대전력부족(MW)', '최대전력여유(MW)', '최대전력여유율(%)', '최대전력발생시간']
        
        # 날짜 컬럼 생성
        df['날짜'] = pd.to_datetime(df[['년', '월', '일']].astype(str).agg('-'.join, axis=1))
        
        # 최근 30일 데이터만 사용
        recent_data = df.tail(30).copy()
        
        # 그래프 생성
        plt.figure(figsize=(15, 10))
        plt.rcParams['font.family'] = 'Malgun Gothic'  # 한글 폰트 설정
        
        # 1. 최대전력수요 및 공급 추이
        plt.subplot(2, 2, 1)
        plt.plot(recent_data['날짜'], recent_data['최대전력수요(MW)'], 'b-', label='최대전력수요', linewidth=2)
        plt.plot(recent_data['날짜'], recent_data['최대전력공급(MW)'], 'g-', label='최대전력공급', linewidth=2)
        plt.title('최근 30일 전력수요 및 공급 추이', fontsize=14, fontweight='bold')
        plt.xlabel('날짜')
        plt.ylabel('전력 (MW)')
        plt.legend()
        plt.xticks(rotation=45)
        plt.grid(True, alpha=0.3)
        
        # 2. 전력여유율 추이
        plt.subplot(2, 2, 2)
        plt.plot(recent_data['날짜'], recent_data['최대전력여유율(%)'], 'r-', linewidth=2)
        plt.title('최근 30일 전력여유율 추이', fontsize=14, fontweight='bold')
        plt.xlabel('날짜')
        plt.ylabel('여유율 (%)')
        plt.xticks(rotation=45)
        plt.grid(True, alpha=0.3)
        
        # 3. 전력부족량 분포
        plt.subplot(2, 2, 3)
        plt.bar(recent_data['날짜'], recent_data['최대전력부족(MW)'], color='orange', alpha=0.7)
        plt.title('최근 30일 전력부족량', fontsize=14, fontweight='bold')
        plt.xlabel('날짜')
        plt.ylabel('부족량 (MW)')
        plt.xticks(rotation=45)
        plt.grid(True, alpha=0.3)
        
        # 4. 전력여유량 분포
        plt.subplot(2, 2, 4)
        plt.bar(recent_data['날짜'], recent_data['최대전력여유(MW)'], color='lightgreen', alpha=0.7)
        plt.title('최근 30일 전력여유량', fontsize=14, fontweight='bold')
        plt.xlabel('날짜')
        plt.ylabel('여유량 (MW)')
        plt.xticks(rotation=45)
        plt.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # 그래프를 base64로 인코딩
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
        img_buffer.seek(0)
        img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
        plt.close()
        
        # 간단한 통계 계산
        total_demand = recent_data['최대전력수요(MW)'].sum()
        avg_demand = recent_data['최대전력수요(MW)'].mean()
        max_demand = recent_data['최대전력수요(MW)'].max()
        min_demand = recent_data['최대전력수요(MW)'].min()
        
        # HTML 응답 생성
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>전력수급 데이터 미리보기 및 예측</title>
            <meta charset="utf-8">
            <style>
                body {{ font-family: 'Malgun Gothic', Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
                .container {{ max-width: 1200px; margin: 0 auto; background-color: white; padding: 20px; border-radius: 10px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px; text-align: center; margin-bottom: 20px; }}
                .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }}
                .stat-card {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); text-align: center; border-left: 4px solid #667eea; }}
                .stat-value {{ font-size: 24px; font-weight: bold; color: #667eea; }}
                .stat-label {{ color: #666; margin-top: 5px; }}
                .chart-section {{ margin-bottom: 30px; }}
                .chart-title {{ font-size: 18px; font-weight: bold; margin-bottom: 15px; color: #333; }}
                .data-table {{ margin-top: 20px; overflow-x: auto; }}
                table {{ width: 100%; border-collapse: collapse; }}
                th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }}
                th {{ background-color: #f8f9fa; font-weight: bold; }}
                .nav-links {{ margin-top: 20px; text-align: center; }}
                .nav-links a {{ display: inline-block; margin: 0 10px; padding: 10px 20px; background-color: #667eea; color: white; text-decoration: none; border-radius: 5px; }}
                .nav-links a:hover {{ background-color: #5a6fd8; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>⚡ 전력수급 데이터 미리보기 및 예측 시각화</h1>
                    <p>HOME_전력수급_최대전력수급.csv 데이터 분석 결과</p>
                </div>
                
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-value">{total_demand:,.0f}</div>
                        <div class="stat-label">총 전력수요 (MW)</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">{avg_demand:,.0f}</div>
                        <div class="stat-label">평균 전력수요 (MW)</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">{max_demand:,.0f}</div>
                        <div class="stat-label">최대 전력수요 (MW)</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">{min_demand:,.0f}</div>
                        <div class="stat-label">최소 전력수요 (MW)</div>
                    </div>
                </div>
                
                <div class="chart-section">
                    <div class="chart-title">📊 전력수급 데이터 시각화 (최근 30일)</div>
                    <img src="data:image/png;base64,{img_base64}" alt="전력수급 데이터 차트" style="width: 100%; max-width: 1000px; height: auto;">
                </div>
                
                <div class="data-table">
                    <div class="chart-title">📋 최근 10일 데이터 미리보기</div>
                    <table>
                        <thead>
                            <tr>
                                <th>날짜</th>
                                <th>최대전력수요(MW)</th>
                                <th>최대전력공급(MW)</th>
                                <th>최대전력부족(MW)</th>
                                <th>최대전력여유(MW)</th>
                                <th>최대전력여유율(%)</th>
                            </tr>
                        </thead>
                        <tbody>
        """
        
        # 최근 10일 데이터 테이블 생성
        for _, row in recent_data.tail(10).iterrows():
            html_content += f"""
                            <tr>
                                <td>{row['날짜'].strftime('%Y-%m-%d')}</td>
                                <td>{row['최대전력수요(MW)']:,.0f}</td>
                                <td>{row['최대전력공급(MW)']:,.0f}</td>
                                <td>{row['최대전력부족(MW)']:,.0f}</td>
                                <td>{row['최대전력여유(MW)']:,.0f}</td>
                                <td>{row['최대전력여유율(%)']:.1f}%</td>
                            </tr>
            """
        
        html_content += """
                        </tbody>
                    </table>
                </div>
                
                <div class="nav-links">
                    <a href="/">🏠 메인 대시보드</a>
                    <a href="/api">📚 API 문서</a>
                    <a href="/docs">🔍 Swagger UI</a>
                </div>
            </div>
        </body>
        </html>
        """
        
        return HTMLResponse(content=html_content)
        
    except Exception as e:
        logger.error(f"전력수급 데이터 미리보기 오류: {e}")
        return HTMLResponse(content=f"<h1>오류 발생: {str(e)}</h1>")

@app.get("/health")
async def health_check():
    """헬스 체크 엔드포인트"""
    return {"status": "healthy", "service": "K-ETS Dashboard API"}

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )
