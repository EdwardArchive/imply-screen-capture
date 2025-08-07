# No Login Dashboard Capture

## 개요
로그인 없이 공개된 대시보드를 캡처할 수 있는 기능입니다.

## 설치

```bash
pip install -r requirements.txt
```

## 사용 방법

### 1. 환경 변수 설정
`.env` 파일에 다음 변수를 추가합니다:

```env
NO_LOGIN_DASHBOARD_URL=http://3.35.136.246:9095/pivot/c/4d56/New_dashboard
SCREENSHOT_DIR=./screenshots
SCREENSHOT_FORMAT=png  # 'png' 또는 'html'
VIEWPORT_WIDTH=1920
VIEWPORT_HEIGHT=1080
```

### 2. 실행

#### 방법 1: main_simple.py 사용 (권장)
```bash
python main_simple.py
```
- HTML 또는 PNG 형식으로 캡처 가능
- `SCREENSHOT_FORMAT=html`: HTML 파일로 저장
- `SCREENSHOT_FORMAT=png`: html2image를 사용하여 PNG로 변환

#### 방법 2: main_soup.py 사용 (wkhtmltoimage 필요)
```bash
# wkhtmltoimage 설치 필요
# Windows: https://wkhtmltopdf.org/downloads.html 에서 다운로드
# Linux: sudo apt-get install wkhtmltopdf
# Mac: brew install wkhtmltopdf

python main_soup.py
```

## 주요 변경사항

1. **SimpleDashboardCapture** (`capture_simple.py`)
   - HTML 형식으로 대시보드 저장
   - 외부 도구 설치 불필요
   - `no_login_dashboard_url` 설정 시 로그인 건너뛰기

2. **DashboardCaptureSoup** (`capture_soup.py`)
   - PNG/이미지 형식으로 대시보드 저장
   - wkhtmltoimage 설치 필요
   - `no_login_dashboard_url` 설정 시 로그인 건너뛰기

3. **main_simple.py** (새로 추가)
   - HTML 캡처용 진입점
   - wkhtmltoimage 없이도 실행 가능

## 문제 해결

### "No wkhtmltoimage executable found" 에러
- `main_simple.py`를 사용하여 HTML로 캡처
- 또는 wkhtmltoimage를 설치 후 `main_soup.py` 사용

### 연결 실패
- 대시보드 URL이 올바른지 확인
- 네트워크 연결 상태 확인
- 방화벽 설정 확인