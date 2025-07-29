# Imply Dashboard Capture - No Browser Version

브라우저를 사용하지 않고 API를 직접 호출하여 대시보드를 캡처하는 실험적인 버전입니다.

## ⚠️ 주의사항

이 방법은 다음과 같은 제한사항이 있습니다:
- JavaScript로 동적 렌더링되는 대시보드는 캡처할 수 없습니다
- Imply가 제공하는 Export API가 있어야 작동합니다
- 대부분의 경우 플레이스홀더 이미지만 생성됩니다
- **권장하지 않는 방법이며, 브라우저 기반 캡처를 사용하는 것이 좋습니다**

## 설치

```bash
cd no_browser
pip install -r requirements.txt
```

## 사용법

```bash
# 상위 디렉토리의 .env 파일을 사용
python main.py
```

## 작동 방식

1. **Export API 시도**: Imply의 대시보드 내보내기 API 호출
2. **데이터 API 시도**: 대시보드 데이터만 가져와서 정보 표시
3. **플레이스홀더 생성**: API가 없는 경우 안내 메시지가 있는 이미지 생성

## 파일 구조

```
no_browser/
├── capture_api.py    # API 기반 캡처 클래스
├── main.py          # 메인 실행 파일
├── requirements.txt # Python 의존성
└── README.md        # 이 문서
```

## 예상 결과

대부분의 경우 실제 대시보드 스크린샷이 아닌 플레이스홀더 이미지가 생성됩니다:
- 대시보드 이름
- API 호출 결과
- 브라우저 기반 캡처 사용 권장 메시지

## 권장 사항

동적 대시보드의 정확한 스크린샷이 필요한 경우, 상위 디렉토리의 브라우저 기반 캡처를 사용하세요:

```bash
cd ..
python main.py
```