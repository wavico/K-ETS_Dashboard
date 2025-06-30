@echo off
chcp 65001 >nul
echo 탄소배출권 대시보드 시작...

REM 메인 앱 실행 (포트 8501)
start "메인 대시보드" cmd /k "streamlit run main.py --server.port 8501"

REM 잠시 대기
timeout /t 3

REM 챗봇 앱 실행 (포트 8502) - 절대 경로 사용
start "AI 챗봇" cmd /k "streamlit run \"pages\5_AI_챗봇.py\" --server.port 8502"

echo 대시보드가 시작되었습니다!
echo 메인 앱: http://localhost:8501
echo 챗봇 앱: http://localhost:8502
pause 