# 🌍 탄소배출권 대시보드 - React 프론트엔드

완전한 플로팅 챗봇 기능이 포함된 React 프론트엔드입니다.

## 🚀 실행 방법

### 1단계: Node.js 설치 확인

```bash
node --version
npm --version
```

### 2단계: 의존성 설치

```bash
npm install
```

### 3단계: Streamlit 백엔드 실행

```bash
# 터미널 1: 메인 대시보드 (포트 8501)
streamlit run main.py --server.port 8501

# 터미널 2: 챗봇 앱 (포트 8502)
streamlit run "pages/5_AI_챗봇.py" --server.port 8502
```

### 4단계: React 프론트엔드 실행

```bash
# 터미널 3: React 앱 (포트 3000)
npm start
```

### 5단계: 브라우저에서 접속

- React 앱: http://localhost:3000
- 메인 대시보드: http://localhost:8501
- 챗봇 앱: http://localhost:8502

## ✨ 주요 기능

### 🎯 완전한 플로팅 챗봇

- **브라우저 전체 기준 fixed 포지션**: 스크롤에 영향받지 않는 진짜 플로팅
- **부드러운 애니메이션**: 슬라이드 인/아웃, 바운스 효과
- **호버 효과**: 마우스 오버 시 스케일 변화
- **반응형 디자인**: 다양한 화면 크기 지원

### 🎨 사이드바 제어 기능

- **플로팅 버튼 클릭 시**: Streamlit 사이드바 자동 닫기
- **우측 챗봇 오버레이**: 전체 화면 높이의 챗봇 패널
- **부드러운 전환**: 0.3초 슬라이드 애니메이션
- **URL 파라미터 제어**: 사이드바 상태를 URL로 관리

### 🎨 UI/UX 특징

- **그라데이션 배경**: 보라색 그라데이션 플로팅 버튼
- **그림자 효과**: 입체적인 시각적 효과
- **부드러운 전환**: 0.3초 애니메이션
- **접근성**: 키보드 네비게이션 지원

### 🔧 기술적 특징

- **React 18**: 최신 React 기능 활용
- **Styled Components**: CSS-in-JS 스타일링
- **Keyframe 애니메이션**: 부드러운 CSS 애니메이션
- **Z-index 관리**: 레이어 우선순위 제어
- **URL 파라미터 제어**: Streamlit 사이드바 상태 동적 제어

## 📁 프로젝트 구조

```
src/
├── App.js                    # 메인 앱 컴포넌트
├── index.js                  # React 진입점
└── components/
    └── FloatingChatbot.js    # 플로팅 챗봇 컴포넌트

public/
└── index.html               # HTML 템플릿

package.json                 # 의존성 관리
```

## 🎮 사용법

1. **플로팅 버튼 클릭**: 우측 하단 🤖 버튼 클릭
2. **사이드바 자동 닫기**: Streamlit 사이드바가 자동으로 닫힘
3. **우측 챗봇 열기**: 우측에서 전체 화면 높이의 챗봇 패널이 슬라이드 인
4. **챗봇 사용**: iframe 내에서 Streamlit 챗봇 사용
5. **챗봇 닫기**: 우측 상단 × 버튼 클릭
6. **사이드바 복원**: 챗봇 닫기 시 사이드바가 자동으로 다시 열림

## 🔧 개발 모드

```bash
# 개발 서버 실행
npm start

# 프로덕션 빌드
npm run build

# 테스트 실행
npm test
```

## 🌟 특징

- **완전한 브라우저 fixed**: Streamlit 제약 없이 진짜 플로팅
- **사이드바 동적 제어**: URL 파라미터로 Streamlit 사이드바 상태 제어
- **우측 오버레이**: 전체 화면 높이의 챗봇 패널
- **부드러운 애니메이션**: CSS keyframe 기반 애니메이션
- **반응형 디자인**: 모바일/태블릿/데스크톱 지원
- **접근성**: 키보드 네비게이션, 스크린 리더 지원
- **성능 최적화**: React 최적화 기법 적용

## 🔧 기술적 구현

### 사이드바 제어

- **URL 파라미터**: `?sidebar=collapsed` / `?sidebar=expanded`
- **Streamlit 연동**: `st.query_params` 사용
- **동적 iframe**: URL 변경 시 iframe 재로드

### 챗봇 오버레이

- **Fixed 포지션**: 우측 전체 화면 높이
- **Transform 애니메이션**: `translateX(100%)` → `translateX(0)`
- **Z-index 관리**: 적절한 레이어 우선순위

## 🐛 문제 해결

### 포트 충돌

```bash
# 다른 포트로 실행
PORT=3001 npm start
```

### CORS 오류

- Streamlit 앱에서 CORS 설정 확인
- 브라우저 개발자 도구에서 오류 확인

### iframe 로딩 실패

- Streamlit 앱이 정상 실행 중인지 확인
- 포트 번호 확인 (8501, 8502)

### 사이드바 제어 안됨

- Streamlit 앱이 URL 파라미터를 지원하는지 확인
- 브라우저 캐시 삭제 후 재시도

## 📞 지원

문제가 발생하면 다음을 확인해주세요:

1. 모든 서비스가 정상 실행 중인지
2. 포트 번호가 올바른지
3. 브라우저 콘솔에 오류가 있는지
4. URL 파라미터가 정상적으로 전달되는지
