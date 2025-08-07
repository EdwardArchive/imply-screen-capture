import os
import sys
from dotenv import load_dotenv
from capture_simple import SimpleDashboardCapture

def main():
    # 환경 변수 로드
    load_dotenv()
    
    # 필수 환경 변수 확인
    imply_base_url = os.getenv('IMPLY_BASE_URL')
    username = os.getenv('IMPLY_USERNAME')
    password = os.getenv('IMPLY_PASSWORD')
    dashboard_urls = os.getenv('DASHBOARD_URLS', os.getenv('DASHBOARD_URL', ''))
    
    if not all([imply_base_url, username, password]):
        print("Missing required environment variables.")
        sys.exit(1)
    
    # URL 리스트 처리
    url_list = []
    if ',' in dashboard_urls:
        url_list = [url.strip() for url in dashboard_urls.split(',') if url.strip()]
    else:
        url_list = [url.strip() for url in dashboard_urls.split('\n') if url.strip()]
    
    print(f"Base URL: {imply_base_url}")
    print(f"Dashboard URLs: {url_list}")
    
    # 캡처 객체 생성
    capture = SimpleDashboardCapture(
        base_url=imply_base_url,
        username=username,
        password=password
    )
    
    # 연결 테스트
    print("\n" + "="*60)
    print("CONNECTION TEST")
    print("="*60)
    capture.test_connection()
    
    # HTML로 저장 시도
    if url_list:
        print("\n" + "="*60)
        print("ATTEMPTING TO SAVE AS HTML")
        print("="*60)
        results = capture.capture_multiple_dashboards(url_list)
        
        print(f"\n{'='*50}")
        print("SUMMARY")
        print(f"{'='*50}")
        
        success_count = sum(1 for r in results if r['success'])
        print(f"Total: {len(results)} | Success: {success_count} | Failed: {len(results) - success_count}")
        
        for result in results:
            if result['success']:
                print(f"✅ {result['dashboard_name']} -> {result['filepath']}")
            else:
                print(f"❌ {result['dashboard_name']} - {result.get('error', 'Unknown error')}")

if __name__ == "__main__":
    main()