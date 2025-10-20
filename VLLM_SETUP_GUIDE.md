# vLLM 설정 가이드

이 가이드는 K-ETS Dashboard에서 Qwen3-30B-A3B 모델을 vLLM으로 실행하는 방법을 안내합니다.

## 📋 목차

1. [필수 요구사항](#필수-요구사항)
2. [vLLM 설치](#vllm-설치)
3. [vLLM 서버 실행](#vllm-서버-실행)
4. [환경 변수 설정](#환경-변수-설정)
5. [애플리케이션 실행](#애플리케이션-실행)
6. [문제 해결](#문제-해결)

---

## 🔧 필수 요구사항

### 하드웨어
- **GPU**: NVIDIA GPU (CUDA 지원)
  - 최소: RTX 3090 (24GB VRAM)
  - 권장: RTX 4090, A100, H100
- **RAM**: 최소 32GB
- **저장공간**: 최소 60GB (모델 다운로드용)

### 소프트웨어
- Python 3.8 이상
- CUDA Toolkit 11.8 이상
- pip

---

## 📦 vLLM 설치

### 1단계: Python 가상환경 활성화

```bash
# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 2단계: vLLM 설치

```bash
# 최신 버전 설치 (권장: vLLM >= 0.8.4)
pip install vllm>=0.8.4

# 또는 특정 버전 설치
pip install vllm==0.8.4
```

### 3단계: 의존성 확인

```bash
pip install transformers accelerate
```

---

## 🚀 vLLM 서버 실행

### Windows

```cmd
# 환경 변수 설정
set VLLM_USE_TRITON_FLASH_ATTN=0

# vLLM 서버 실행
venv\Scripts\python.exe -m vllm.entrypoints.openai.api_server ^
  --model Qwen/Qwen3-30B-A3B ^
  --host 0.0.0.0 ^
  --port 8000 ^
  --served-model-name gpt-4-turbo ^
  --trust-remote-code
```

### Linux/Mac

```bash
# 환경 변수 설정
export VLLM_USE_TRITON_FLASH_ATTN=0

# vLLM 서버 실행
python -m vllm.entrypoints.openai.api_server \
  --model Qwen/Qwen3-30B-A3B \
  --host 0.0.0.0 \
  --port 8000 \
  --served-model-name gpt-4-turbo \
  --trust-remote-code
```

### 서버 옵션 설명

| 옵션 | 설명 |
|------|------|
| `--model` | 사용할 모델 (HuggingFace 모델 ID) |
| `--host` | 서버 호스트 (0.0.0.0은 모든 인터페이스) |
| `--port` | 서버 포트 (기본: 8000) |
| `--served-model-name` | API에서 사용할 모델 이름 |
| `--trust-remote-code` | 원격 코드 실행 허용 (Qwen 모델에 필요) |

### 다른 모델 사용하기

Qwen2.5-3B-Instruct (더 가벼운 모델):
```bash
python -m vllm.entrypoints.openai.api_server \
  --model Qwen/Qwen2.5-3B-Instruct \
  --host 0.0.0.0 \
  --port 8000 \
  --served-model-name gpt-4-turbo
```

---

## ⚙️ 환경 변수 설정

### 1단계: .env 파일 생성

`.env.example` 파일을 `.env`로 복사:

```bash
# Windows
copy .env.example .env

# Linux/Mac
cp .env.example .env
```

### 2단계: vLLM 설정 확인

`.env` 파일에서 다음 설정 확인:

```env
# vLLM 사용 활성화
USE_VLLM=true

# vLLM 서버 주소
VLLM_BASE_URL=http://localhost:8000/v1

# 서버에서 설정한 모델 이름과 동일해야 함
VLLM_MODEL_NAME=gpt-4-turbo

# API 키 (vLLM은 불필요하지만 호환성 유지)
VLLM_API_KEY=EMPTY
```

### 3단계: 임베딩 모델 설정 (선택사항)

vLLM은 텍스트 생성만 담당하므로, 임베딩은 외부 API 사용:

```env
# Upstage 또는 OpenAI 중 하나 설정
UPSTAGE_API_KEY=your-upstage-api-key
# 또는
OPENAI_API_KEY=your-openai-api-key
```

---

## 🎯 애플리케이션 실행

### 1단계: vLLM 서버 상태 확인

새 터미널에서 다음 명령어로 서버가 정상 동작하는지 확인:

```bash
curl http://localhost:8000/v1/models
```

정상 응답 예시:
```json
{
  "object": "list",
  "data": [
    {
      "id": "gpt-4-turbo",
      "object": "model",
      "created": 1234567890,
      "owned_by": "vllm"
    }
  ]
}
```

### 2단계: FastAPI 서버 실행

```bash
# Windows
venv\Scripts\python.exe -m uvicorn app.main:app --reload

# Linux/Mac
python -m uvicorn app.main:app --reload
```

### 3단계: Streamlit 앱 실행 (선택사항)

```bash
# Windows
venv\Scripts\streamlit run Home.py

# Linux/Mac
streamlit run Home.py
```

---

## 🔍 문제 해결

### 서버가 시작되지 않는 경우

**증상**: `CUDA out of memory` 오류

**해결책**:
1. 더 작은 모델 사용 (Qwen2.5-3B-Instruct)
2. GPU 메모리 확인: `nvidia-smi`
3. `--max-model-len` 옵션으로 메모리 사용량 제한:
   ```bash
   --max-model-len 2048
   ```

### 모델 다운로드가 느린 경우

**해결책**: HuggingFace 미러 사용
```bash
export HF_ENDPOINT=https://hf-mirror.com
```

### API 연결 오류

**증상**: `Connection refused` 또는 `Failed to connect`

**해결책**:
1. vLLM 서버가 실행 중인지 확인
2. 포트가 올바른지 확인: `netstat -an | findstr 8000`
3. 방화벽 설정 확인

### 성능이 느린 경우

**해결책**:
1. `--tensor-parallel-size` 옵션으로 GPU 병렬화:
   ```bash
   --tensor-parallel-size 2  # 2개 GPU 사용
   ```
2. `--gpu-memory-utilization` 조정:
   ```bash
   --gpu-memory-utilization 0.95  # GPU 메모리 95% 사용
   ```

### vLLM에서 외부 API로 전환

`.env` 파일 수정:
```env
USE_VLLM=false
OPENAI_API_KEY=your-actual-openai-key
```

---

## 📊 벤치마크

### Qwen3-30B-A3B 성능

| 항목 | 사양 |
|------|------|
| 모델 크기 | 30B 파라미터 (3B 활성화) |
| VRAM 사용량 | ~20GB |
| 추론 속도 | ~30 tokens/sec (RTX 4090) |
| 컨텍스트 길이 | 최대 32K tokens |

### 모델 비교

| 모델 | 파라미터 | VRAM | 속도 | 품질 |
|------|----------|------|------|------|
| Qwen3-30B-A3B | 30B (3B 활성) | ~20GB | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| Qwen2.5-3B | 3B | ~8GB | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| GPT-4-Turbo (API) | - | 0GB | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

---

## 🔗 추가 리소스

- [vLLM 공식 문서](https://docs.vllm.ai/)
- [Qwen3 모델 페이지](https://github.com/QwenLM/Qwen3)
- [HuggingFace Qwen3-30B-A3B](https://huggingface.co/Qwen/Qwen3-30B-A3B)

---

## ✅ 체크리스트

설정 완료 전 확인 사항:

- [ ] Python 가상환경 활성화
- [ ] vLLM 설치 (>= 0.8.4)
- [ ] GPU 메모리 확인 (최소 20GB)
- [ ] vLLM 서버 실행 및 정상 동작 확인
- [ ] `.env` 파일 생성 및 설정
- [ ] `USE_VLLM=true` 확인
- [ ] 임베딩 API 키 설정 (Upstage 또는 OpenAI)
- [ ] 애플리케이션 실행 테스트

---

문제가 발생하면 [GitHub Issues](https://github.com/vllm-project/vllm/issues)에서 유사한 문제를 검색하거나 새 이슈를 생성하세요.
