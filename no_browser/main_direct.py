import os
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from capture_direct import DirectDashboardCapture


def main():
    # 환경 변수 로드
    load_dotenv()
    
    # 대시보드 URL 확인
    dashboard_urls = os.getenv('DASHBOARD_URLS', os.getenv('DASHBOARD_URL', ''))
    
    if not dashboard_urls:
        print("Missing DASHBOARD_URLS (or DASHBOARD_URL) in .env file")
        sys.exit(1)
    
    # 대시보드 URL 리스트 처리
    url_list = []
    if ',' in dashboard_urls:
        # 쉼표로 구분
        url_list = [url.strip() for url in dashboard_urls.split(',') if url.strip()]
    else:
        # 줄바꿈으로 구분 또는 단일 URL
        url_list = [url.strip() for url in dashboard_urls.split('\n') if url.strip()]
    
    if not url_list:
        print("No valid dashboard URLs found.")
        sys.exit(1)
    
    print(f"Found {len(url_list)} dashboard(s) to analyze")
    print("\n" + "="*70)
    print("⚠️  IMPORTANT NOTICE:")
    print("This tool CANNOT capture actual dashboard screenshots without a browser.")
    print("It only checks if the URLs are accessible and creates info images.")
    print("For real screenshots, use the browser-based version in the parent directory.")
    print("="*70 + "\n")
    
    # 선택적 인증 정보
    session_cookie = os.getenv('SESSION_COOKIE')
    auth_token = os.getenv('AUTH_TOKEN')
    
    if session_cookie or auth_token:
        print("Using provided authentication credentials")
    else:
        print("No authentication credentials provided - direct access only")
    
    try:
        # 캡처 객체 생성
        capture = DirectDashboardCapture(
            session_cookie=session_cookie,
            auth_token=auth_token,
            config={
                'screenshot_dir': os.getenv('SCREENSHOT_DIR', './screenshots'),
                'format': os.getenv('SCREENSHOT_FORMAT', 'png'),
                'timeout': 30
            }
        )
        
        # 대시보드 처리
        if len(url_list) == 1:
            # 단일 대시보드
            print(f"Analyzing dashboard: {url_list[0]}")
            result = capture.capture_dashboard(url_list[0])
            
            print(f"\nResult:")
            if result['success']:
                print(f"✅ Info saved: {result['filepath']}")
                if 'info' in result:
                    print("\nAccess Information:")
                    for key, value in result['info'].items():
                        print(f"  {key}: {value}")
            else:
                print(f"❌ Failed: {result.get('error', 'Unknown error')}")
        else:
            # 여러 대시보드
            print(f"Analyzing {len(url_list)} dashboards...")
            results = capture.capture_multiple_dashboards(url_list)
            
            # 결과 요약
            print(f"\n{'='*50}")
            print("ANALYSIS SUMMARY")
            print(f"{'='*50}")
            
            success_count = sum(1 for r in results if r['success'])
            print(f"Total: {len(results)} | Success: {success_count} | Failed: {len(results) - success_count}")
            
            print("\nDetails:")
            for result in results:
                if result['success']:
                    print(f"✅ {result['dashboard_name']} -> {result['filepath']}")
                else:
                    print(f"❌ {result['dashboard_name']} - {result.get('error', 'Unknown error')}")
                
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()