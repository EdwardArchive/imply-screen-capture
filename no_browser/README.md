# BeautifulSoup 기반 대시보드 캡처

이 버전은 Selenium/Playwright 대신 BeautifulSoup과 requests를 사용하여 대시보드를 캡처합니다.

## 주요 특징

- 웹드라이버(Chrome/Chromium) 불필요
- BeautifulSoup으로 HTML 파싱
- imgkit(wkhtmltoimage)를 사용한 HTML→이미지 변환
- requests 세션을 통한 로그인 상태 유지

## 필수 요구사항

### 1. Python 패키지 설치
```bash
pip install -r requirements.txt
```

### 2. wkhtmltoimage 설치

이 도구는 HTML을 이미지로 변환하기 위해 wkhtmltoimage가 필요합니다.

#### Windows:
1. https://wkhtmltopdf.org/downloads.html 에서 다운로드
2. 설치 후 환경 변수에 경로 추가하거나 `.env`에 경로 지정

#### Linux:
```bash
sudo apt-get install wkhtmltopdf
```

#### macOS:
```bash
brew install --cask wkhtmltopdf
```

## 환경 변수 설정

`.env` 파일 생성:
```
IMPLY_BASE_URL=https://your-imply-instance.com
IMPLY_USERNAME=your_username
IMPLY_PASSWORD=your_password
DASHBOARD_URLS=https://your-imply-instance.com/pivot/datasource/dashboard1,https://your-imply-instance.com/pivot/datasource/dashboard2

# 선택사항
SCREENSHOT_DIR=./screenshots
SCREENSHOT_FORMAT=png
DASHBOARD_WAIT_TIME=5000
WKHTMLTOIMAGE_PATH=C:\Program Files\wkhtmltopdf\bin\wkhtmltoimage.exe  # Windows 예시
```

## 사용 방법

```bash
python main_soup.py
```

## 제한사항

- JavaScript 렌더링이 필요한 동적 대시보드는 제대로 캡처되지 않을 수 있음
- 복잡한 인터랙티브 차트는 정적 상태로만 캡처됨
- 실시간 데이터 업데이트는 캡처되지 않음

## 대안

완전한 JavaScript 렌더링이 필요한 경우, 원본 Playwright 기반 버전을 사용하세요.