import os
import sys
from dotenv import load_dotenv
from capture_soup import DashboardCaptureSoup


def main():
    # 환경 변수 로드
    load_dotenv()
    
    # 환경 변수 확인
    imply_base_url = os.getenv('IMPLY_BASE_URL')
    username = os.getenv('IMPLY_USERNAME')
    password = os.getenv('IMPLY_PASSWORD')
    dashboard_urls = os.getenv('DASHBOARD_URLS', os.getenv('DASHBOARD_URL', ''))
    no_login_dashboard_url = os.getenv('NO_LOGIN_DASHBOARD_URL')
    
    # no_login_dashboard_url이 설정되어 있으면 다른 필수 변수 체크 스킵
    if no_login_dashboard_url:
        print("NO_LOGIN_DASHBOARD_URL is set - will skip login")
        if not imply_base_url:
            imply_base_url = no_login_dashboard_url  # base_url 대신 사용
    elif not all([imply_base_url, username, password, dashboard_urls]):
        print("Missing required environment variables. Please check your .env file.")
        print("Required: IMPLY_BASE_URL, IMPLY_USERNAME, IMPLY_PASSWORD, DASHBOARD_URLS (or DASHBOARD_URL)")
        print("Or set NO_LOGIN_DASHBOARD_URL to skip login")
        sys.exit(1)
    
    # 대시보드 URL 리스트 처리
    url_list = []
    if no_login_dashboard_url:
        # no_login_dashboard_url이 설정되어 있으면 이것만 사용
        url_list = [no_login_dashboard_url]
    elif ',' in dashboard_urls:
        # 쉼표로 구분
        url_list = [url.strip() for url in dashboard_urls.split(',') if url.strip()]
    else:
        # 줄바꿈으로 구분 또는 단일 URL
        url_list = [url.strip() for url in dashboard_urls.split('\n') if url.strip()]
    
    if not url_list:
        print("No valid dashboard URLs found.")
        sys.exit(1)
    
    print(f"Found {len(url_list)} dashboard(s) to capture")
    
    try:
        # 캡처 객체 생성
        capture = DashboardCaptureSoup(
            base_url=imply_base_url,
            username=username or '',
            password=password or '',
            config={
                'screenshot_dir': os.getenv('SCREENSHOT_DIR', './screenshots'),
                'format': os.getenv('SCREENSHOT_FORMAT', 'png'),
                'wait_time': int(os.getenv('DASHBOARD_WAIT_TIME', '5000')),
                'wkhtmltoimage_path': os.getenv('WKHTMLTOIMAGE_PATH', None),  # Optional path to wkhtmltoimage
                'no_login_dashboard_url': no_login_dashboard_url
            }
        )
        
        # 대시보드 캡처
        if len(url_list) == 1:
            # 단일 대시보드
            print(f"Capturing single dashboard: {url_list[0]}")
            result = capture.capture_dashboard(url_list[0])
            print(f"\nCapture result:")
            if result['success']:
                print(f"✅ Success: {result['dashboard_name']} -> {result['filepath']}")
            else:
                print(f"❌ Failed: {result['dashboard_name']} - {result.get('error', 'Unknown error')}")
        else:
            # 여러 대시보드
            print(f"Capturing {len(url_list)} dashboards...")
            results = capture.capture_multiple_dashboards(url_list)
            
            # 결과 요약
            print(f"\n{'='*50}")
            print("CAPTURE SUMMARY")
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