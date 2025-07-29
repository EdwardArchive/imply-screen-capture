# Imply Dashboard Capture - No Browser Version

브라우저를 사용하지 않고 대시보드 URL에 직접 접근하여 정보를 수집하는 도구입니다.

## ⚠️ 중요 안내

**이 도구는 실제 대시보드 스크린샷을 캡처할 수 없습니다!**
- Imply는 로그인 API를 제공하지 않음
- 대시보드는 JavaScript로 동적 렌더링됨
- 브라우저 없이는 실제 화면을 캡처할 수 없음
- **대신 접근 가능 여부와 응답 정보만 확인 가능**

## 설치

```bash
cd no_browser
pip install -r requirements.txt
```

## 사용법

### 기본 사용 (인증 없이)
```bash
python main_direct.py
```

### 인증 정보와 함께 사용 (선택사항)
`.env` 파일에 추가:
```env
# 선택사항 - 브라우저에서 얻은 세션 쿠키나 토큰
SESSION_COOKIE=your_session_cookie_value
AUTH_TOKEN=your_auth_token
```

## 작동 방식

1. **직접 URL 접근**: 대시보드 URL에 HTTP 요청
2. **응답 분석**: 상태 코드, 리다이렉션, 콘텐츠 타입 확인
3. **정보 이미지 생성**: 수집된 정보를 이미지로 저장

## 생성되는 이미지

실제 대시보드가 아닌 다음 정보를 담은 이미지:
- 대시보드 URL
- HTTP 상태 코드
- 콘텐츠 타입
- 접근 결과 (로그인 페이지로 리다이렉션, HTML 수신 등)

## 파일 구조

```
no_browser/
├── capture_direct.py  # 직접 접근 클래스
├── main_direct.py     # 메인 실행 파일
├── requirements.txt   # Python 의존성
└── README.md         # 이 문서
```

## 실제 스크린샷이 필요한 경우

브라우저 기반 캡처를 사용하세요:

```bash
cd ..
python main.py
```

브라우저 기반 버전만이 실제 대시보드를 렌더링하고 스크린샷을 캡처할 수 있습니다.