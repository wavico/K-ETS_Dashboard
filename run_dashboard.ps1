Write-Host "탄소배출권 대시보드 시작..." -ForegroundColor Green

# 메인 앱 실행 (포트 8501)
Start-Process powershell -ArgumentList "-NoExit", "-Command", "streamlit run main.py --server.port 8501"

# 잠시 대기
Start-Sleep -Seconds 3

# 챗봇 앱 실행 (포트 8502) - 따옴표로 경로 감싸기
Start-Process powershell -ArgumentList "-NoExit", "-Command", "streamlit run 'pages\5_AI_챗봇.py' --server.port 8502"

Write-Host "대시보드가 시작되었습니다!" -ForegroundColor Yellow
Write-Host "메인 앱: http://localhost:8501" -ForegroundColor Cyan
Write-Host "챗봇 앱: http://localhost:8502" -ForegroundColor Cyan 