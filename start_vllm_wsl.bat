@echo off
REM vLLM 서버 시작 스크립트 (WSL Ubuntu에서 실행)
REM Qwen2.5-3B-Instruct 모델 사용 (12GB VRAM에 최적화)

echo ========================================
echo vLLM 서버 시작 중 (WSL Ubuntu)
echo 모델: Qwen/Qwen2.5-3B-Instruct
echo GPU: RTX 5070 Ti (12GB VRAM)
echo ========================================
echo.

echo WSL Ubuntu에서 vLLM 서버를 시작합니다...
echo 첫 실행 시 모델 다운로드에 시간이 걸릴 수 있습니다 (~6GB)
echo 다운로드 위치: ~/.cache/huggingface/hub/
echo.
echo 서버가 시작되면 http://localhost:8000 에서 접근 가능합니다.
echo.

REM WSL에서 vLLM 서버 실행
wsl -d Ubuntu bash -c "cd ~ && source vllm_env/bin/activate && export VLLM_USE_TRITON_FLASH_ATTN=0 && vllm serve Qwen/Qwen2.5-3B-Instruct --host 0.0.0.0 --port 8000 --served-model-name gpt-4-turbo --gpu-memory-utilization 0.85 --max-model-len 4096"

pause
