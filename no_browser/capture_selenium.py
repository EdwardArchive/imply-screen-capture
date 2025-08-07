import os
import time
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, List
from urllib.parse import urlparse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import base64

# SSL 경고 비활성화
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class SeleniumDashboardCapture:
    def __init__(self, base_url: str, username: str, password: str, config: Optional[Dict] = None):
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.password = password
        self.config = {
            'screenshot_dir': './screenshots',
            'format': 'png',
            'timeout': 30,
            'wait_time': 5,
            'viewport': {'width': 1920, 'height': 1080},
            'no_login_dashboard_url': None,
            'headless': True,
            **(config or {})
        }
        self.driver = None
        
    def ensure_screenshot_dir(self):
        """스크린샷 디렉토리가 존재하는지 확인하고 없으면 생성합니다."""
        Path(self.config['screenshot_dir']).mkdir(parents=True, exist_ok=True)
    
    def extract_dashboard_name(self, url: str) -> str:
        """URL에서 대시보드 이름을 추출합니다."""
        parsed = urlparse(url)
        path_parts = parsed.path.rstrip('/').split('/')
        
        if path_parts:
            dashboard_name = path_parts[-1]
            return "".join(c if c.isalnum() or c in '-_' else '_' for c in dashboard_name)
        
        return "dashboard"
    
    def generate_filename(self, dashboard_name: str) -> str:
        """스크린샷 파일명을 생성합니다."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return f"{dashboard_name}_{timestamp}.{self.config['format']}"
    
    def setup_driver(self):
        """Selenium WebDriver를 설정합니다."""
        chrome_options = Options()
        
        if self.config['headless']:
            chrome_options.add_argument('--headless')
        
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument(f"--window-size={self.config['viewport']['width']},{self.config['viewport']['height']}")
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument('--allow-insecure-localhost')
        
        # Chrome 버전에 따른 설정
        chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
        except:
            # ChromeDriver가 PATH에 없는 경우를 위한 대체 방법
            try:
                from webdriver_manager.chrome import ChromeDriverManager
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
            except:
                print("Chrome WebDriver를 찾을 수 없습니다. 다음 방법 중 하나를 시도하세요:")
                print("1. ChromeDriver를 다운로드하고 PATH에 추가")
                print("2. pip install webdriver-manager 실행")
                raise
    
    def close_driver(self):
        """WebDriver를 종료합니다."""
        if self.driver:
            self.driver.quit()
            self.driver = None
    
    def capture_url_to_image(self, url: str) -> Dict:
        """URL을 이미지로 캡처합니다."""
        dashboard_name = self.extract_dashboard_name(url)
        
        try:
            if not self.driver:
                self.setup_driver()
            
            print(f"Navigating to: {url}")
            self.driver.get(url)
            
            # 페이지 로드 대기
            time.sleep(self.config['wait_time'])
            
            # JavaScript 실행 완료 대기
            WebDriverWait(self.driver, self.config['timeout']).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
            
            # 추가 대기 (동적 콘텐츠 로드)
            time.sleep(2)
            
            # 스크린샷 저장
            filename = self.generate_filename(dashboard_name)
            filepath = os.path.join(self.config['screenshot_dir'], filename)
            
            # 전체 페이지 스크린샷
            if self.config.get('full_page', False):
                # 전체 페이지 높이 계산
                total_height = self.driver.execute_script("return document.body.scrollHeight")
                self.driver.set_window_size(self.config['viewport']['width'], total_height)
                time.sleep(1)
            
            self.driver.save_screenshot(filepath)
            print(f"📸 Screenshot saved: {filepath}")
            
            return {
                'success': True,
                'filepath': filepath,
                'filename': filename,
                'dashboard_name': dashboard_name,
                'dashboard_url': url
            }
            
        except Exception as e:
            print(f"❌ Failed to capture dashboard: {e}")
            return {
                'success': False,
                'dashboard_name': dashboard_name,
                'dashboard_url': url,
                'error': str(e)
            }
    
    def capture_html_to_image(self, html_content: str, output_path: str) -> bool:
        """HTML 콘텐츠를 이미지로 변환합니다."""
        try:
            if not self.driver:
                self.setup_driver()
            
            # Data URL로 HTML 로드
            html_base64 = base64.b64encode(html_content.encode()).decode()
            data_url = f"data:text/html;base64,{html_base64}"
            
            self.driver.get(data_url)
            time.sleep(self.config['wait_time'])
            
            # 스크린샷 저장
            self.driver.save_screenshot(output_path)
            return True
            
        except Exception as e:
            print(f"❌ Failed to convert HTML to image: {e}")
            return False
    
    def capture_dashboard(self, dashboard_url: str) -> Dict:
        """대시보드를 캡처합니다."""
        self.ensure_screenshot_dir()
        
        try:
            # no_login_dashboard_url이 설정되어 있으면 로그인 없이 직접 캡처
            if self.config.get('no_login_dashboard_url'):
                print("Using no_login_dashboard_url - skipping login")
                return self.capture_url_to_image(self.config['no_login_dashboard_url'])
            
            # 일반 URL 캡처
            return self.capture_url_to_image(dashboard_url)
            
        finally:
            # 단일 캡처 후 드라이버 종료
            self.close_driver()
    
    def capture_multiple_dashboards(self, dashboard_urls: List[str]) -> List[Dict]:
        """여러 대시보드를 캡처합니다."""
        self.ensure_screenshot_dir()
        results = []
        
        try:
            # 드라이버 한 번만 초기화
            self.setup_driver()
            
            for i, url in enumerate(dashboard_urls):
                print(f"\n{'='*50}")
                print(f"Processing dashboard {i+1}/{len(dashboard_urls)}: {url}")
                print(f"{'='*50}")
                
                # no_login_dashboard_url이 설정되어 있으면 그것을 사용
                if self.config.get('no_login_dashboard_url'):
                    result = self.capture_url_to_image(self.config['no_login_dashboard_url'])
                else:
                    result = self.capture_url_to_image(url)
                
                results.append(result)
            
        finally:
            # 모든 캡처 완료 후 드라이버 종료
            self.close_driver()
        
        return results