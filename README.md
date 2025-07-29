# Imply Dashboard Screen Capture (Python)

Playwright를 사용하여 Imply 대시보드를 자동으로 캡처하는 Python 도구입니다. 헤드리스 모드로 실행되어 리눅스 서버 환경에 최적화되어 있습니다.

## 주요 기능

- 브라우저 자동화를 통한 Imply 로그인
- 대시보드 자동 스크린샷 캡처
- 헤드리스 모드 지원 (서버 환경)
- 환경 변수 기반 설정

## 요구사항

- Python 3.7+
- Playwright
- Chromium 브라우저

## 설치

### 1. 의존성 설치

```bash
cd python
pip install -r requirements.txt
```

### 2. Playwright 브라우저 설치

```bash
# 시스템 의존성과 함께 설치 (권장)
python -m playwright install --with-deps chromium

# 또는 Chromium만 설치
playwright install chromium
```

## 설정

### 1. 환경 변수 파일 생성

```bash
cp .env.example .env
```

### 2. `.env` 파일 수정

```env
# Imply 서버 정보
IMPLY_BASE_URL=http://your-imply-server.com:9095/
IMPLY_USERNAME=your@email.com
IMPLY_PASSWORD=yourpassword

# 캡처할 대시보드 URL (쉼표로 구분하여 여러 개 가능)
DASHBOARD_URLS=http://your-imply-server.com:9095/pivot/dashboard1,http://your-imply-server.com:9095/pivot/dashboard2
# 또는 단일 URL (하위 호환성)
# DASHBOARD_URL=http://your-imply-server.com:9095/pivot/dashboard-id

# 대시보드 로드 대기 시간 (밀리초)
DASHBOARD_WAIT_TIME=5000

# 스크린샷 저장 경로
SCREENSHOT_DIR=./screenshots

# 스크린샷 형식 (png/jpeg)
SCREENSHOT_FORMAT=png
```

## 사용법

### 기본 실행

```bash
python main.py
```

실행 시 다음과 같은 작업이 수행됩니다:
1. Imply 로그인 페이지 접속
2. 자동 로그인 (이메일/비밀번호 입력)
3. 지정된 대시보드로 이동
4. 스크린샷 캡처 및 저장

### 프로그래밍 방식 사용

```python
from capture import DashboardCapture

# 캡처 객체 생성
capture = DashboardCapture(
    base_url="http://imply-server.com:9095/",
    username="user@email.com",
    password="password",
    config={
        'headless': True,
        'wait_time': 5000,
        'screenshot_dir': './screenshots'
    }
)

# 단일 대시보드 캡처
result = capture.capture_dashboard_sync(
    "http://imply-server.com:9095/pivot/test-dashboard"
)
print(f"Screenshot saved: {result['filepath']}")

# 여러 대시보드 캡처
urls = [
    "http://imply-server.com:9095/pivot/sales-dashboard",
    "http://imply-server.com:9095/pivot/metrics-dashboard"
]
results = capture.capture_multiple_dashboards_sync(urls)

for result in results:
    if result['success']:
        print(f"✅ {result['dashboard_name']} -> {result['filepath']}")
    else:
        print(f"❌ {result['dashboard_name']} failed: {result['error']}")
```

## 파일 구조

```
python/
├── .env.example      # 환경 변수 예제
├── capture.py        # 대시보드 캡처 기능
├── main.py           # 메인 실행 파일
├── requirements.txt  # Python 의존성
└── README.md         # 문서
```

## 주요 기능 상세

### URL에서 대시보드 이름 추출
- URL의 마지막 경로가 자동으로 파일명에 포함됩니다
- 예: `http://server.com/pivot/sales-report` → `sales-report_20241129_143022.png`

### 여러 대시보드 캡처
- `DASHBOARD_URLS`에 쉼표로 구분하여 여러 URL 지정 가능
- 각 대시보드는 순차적으로 캡처됩니다
- 결과는 요약되어 표시됩니다

## 리눅스 서버 설정

### Ubuntu/Debian:
```bash
# 필요한 의존성 설치
sudo apt-get update
sudo apt-get install -y \
    libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 \
    libcups2 libdrm2 libxkbcommon0 libxcomposite1 \
    libxdamage1 libxfixes3 libxrandr2 libgbm1 libasound2
```

### CentOS/RHEL:
```bash
sudo yum install -y \
    nss nspr atk at-spi2-atk cups-libs \
    libdrm libxkbcommon libXcomposite libXdamage \
    libXfixes libXrandr mesa-libgbm alsa-lib
```

## 문제 해결

### 1. 로그인 실패
- `.env` 파일의 인증 정보 확인
- Imply 서버 URL 끝에 `/` 포함 여부 확인
- 로그인 페이지의 HTML 구조 변경 시 `capture.py`의 선택자 수정 필요

### 2. 스크린샷이 비어있음
- `DASHBOARD_WAIT_TIME` 값을 늘려서 대시보드 로드 시간 확보
- 네트워크 연결 상태 확인

### 3. 리눅스 서버에서 실행 오류
- 시스템 의존성 설치 확인
- `playwright install --with-deps chromium` 실행

## 주의사항

- 헤드리스 모드로 실행되므로 GUI가 없는 서버 환경에서도 동작
- 대시보드 복잡도에 따라 `DASHBOARD_WAIT_TIME` 조정 필요
- 로그인 페이지 구조가 변경되면 코드 수정 필요