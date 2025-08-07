import os
import time
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, List
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
import json
try:
    from html2image import Html2Image
    HTML2IMAGE_AVAILABLE = True
except ImportError:
    HTML2IMAGE_AVAILABLE = False
    print("Warning: html2image not installed. Image conversion will not be available.")

# SSL 경고 비활성화
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class SimpleDashboardCapture:
    def __init__(self, base_url: str, username: str, password: str, config: Optional[Dict] = None):
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.password = password
        self.config = {
            'screenshot_dir': './screenshots',
            'format': 'html',  # 'html' 또는 'png'
            'timeout': 30,
            'no_login_dashboard_url': None,  # 로그인 없이 접근 가능한 대시보드 URL
            'viewport': {'width': 1920, 'height': 1080},
            **(config or {})
        }
        self.session = None
        self._is_logged_in = False
        
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
    
    def generate_filename(self, dashboard_name: str, ext: Optional[str] = None) -> str:
        """스크린샷 파일명을 생성합니다."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        extension = ext or self.config['format']
        return f"{dashboard_name}_{timestamp}.{extension}"
    
    def test_connection(self) -> bool:
        """서버 연결을 테스트합니다."""
        try:
            print(f"Testing connection to: {self.base_url}")
            
            # 다양한 방법으로 연결 시도
            methods = [
                ('requests.get', lambda: requests.get(self.base_url, timeout=5, verify=False, allow_redirects=False)),
                ('requests with headers', lambda: requests.get(
                    self.base_url, 
                    timeout=5, 
                    verify=False,
                    headers={
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                        'Accept': '*/*'
                    }
                )),
                ('urllib', lambda: __import__('urllib.request').request.urlopen(self.base_url, timeout=5))
            ]
            
            for method_name, method in methods:
                try:
                    print(f"  Trying {method_name}...")
                    response = method()
                    print(f"  ✅ {method_name} succeeded")
                    if hasattr(response, 'status_code'):
                        print(f"     Status: {response.status_code}")
                        print(f"     Headers: {dict(response.headers)}")
                    return True
                except Exception as e:
                    print(f"  ❌ {method_name} failed: {type(e).__name__}: {str(e)}")
                    
            return False
            
        except Exception as e:
            print(f"Connection test failed: {e}")
            return False
    
    def login_with_cookies(self) -> bool:
        """쿠키 파일을 사용하여 로그인 상태를 복원합니다."""
        cookie_file = os.path.join(os.path.dirname(__file__), 'cookies.json')
        
        if os.path.exists(cookie_file):
            try:
                with open(cookie_file, 'r') as f:
                    cookies = json.load(f)
                
                self.session = requests.Session()
                for cookie in cookies:
                    self.session.cookies.set(cookie['name'], cookie['value'])
                
                print("✅ Loaded cookies from file")
                self._is_logged_in = True
                return True
            except Exception as e:
                print(f"Failed to load cookies: {e}")
        
        return False
    
    def save_html_dashboard(self, dashboard_url: str) -> Dict:
        """대시보드 HTML을 저장합니다."""
        dashboard_name = self.extract_dashboard_name(dashboard_url)
        
        try:
            if not self.session:
                self.session = requests.Session()
                self.session.verify = False
            
            print(f"Fetching dashboard: {dashboard_url}")
            
            # 쿠키가 있다면 사용
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            }
            
            response = self.session.get(
                dashboard_url,
                headers=headers,
                timeout=self.config['timeout'],
                allow_redirects=True
            )
            
            if response.status_code != 200:
                raise Exception(f"HTTP {response.status_code}")
            
            # HTML 저장 또는 이미지 변환
            if self.config['format'] == 'html':
                filename = self.generate_filename(dashboard_name)
                filepath = os.path.join(self.config['screenshot_dir'], filename)
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(response.text)
                
                print(f"📄 HTML saved: {filepath}")
            elif self.config['format'] == 'png' and HTML2IMAGE_AVAILABLE:
                # HTML을 이미지로 변환
                hti = Html2Image(
                    output_path=self.config['screenshot_dir'],
                    size=(self.config['viewport']['width'], self.config['viewport']['height'])
                )
                
                filename_base = self.generate_filename(dashboard_name, 'png')
                files = hti.screenshot(
                    html_str=response.text,
                    save_as=filename_base
                )
                
                if files:
                    filepath = os.path.join(self.config['screenshot_dir'], files[0])
                    print(f"📸 Screenshot saved: {filepath}")
                else:
                    raise Exception("Failed to create image from HTML")
            else:
                # PNG 형식이지만 html2image가 없는 경우 HTML로 저장
                print("Warning: html2image not available, saving as HTML instead")
                filename = self.generate_filename(dashboard_name, 'html')
                filepath = os.path.join(self.config['screenshot_dir'], filename)
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(response.text)
                
                print(f"📄 HTML saved: {filepath} (PNG conversion not available)")
            
            return {
                'success': True,
                'filepath': filepath,
                'filename': os.path.basename(filepath),
                'dashboard_name': dashboard_name,
                'dashboard_url': dashboard_url
            }
            
        except Exception as e:
            print(f"❌ Failed to capture dashboard: {e}")
            return {
                'success': False,
                'dashboard_name': dashboard_name,
                'dashboard_url': dashboard_url,
                'error': str(e)
            }
    
    def capture_dashboard(self, dashboard_url: str) -> Dict:
        """대시보드를 캡처합니다."""
        self.ensure_screenshot_dir()
        
        # no_login_dashboard_url이 설정되어 있으면 로그인 없이 직접 캡처
        if self.config.get('no_login_dashboard_url'):
            print("Using no_login_dashboard_url - skipping login")
            return self.save_html_dashboard(self.config['no_login_dashboard_url'])
        
        # 연결 테스트
        if not self.test_connection():
            return {
                'success': False,
                'dashboard_name': self.extract_dashboard_name(dashboard_url),
                'dashboard_url': dashboard_url,
                'error': 'Connection test failed'
            }
        
        # HTML 저장 시도
        return self.save_html_dashboard(dashboard_url)
    
    def capture_multiple_dashboards(self, dashboard_urls: List[str]) -> List[Dict]:
        """여러 대시보드를 캡처합니다."""
        self.ensure_screenshot_dir()
        results = []
        
        for i, url in enumerate(dashboard_urls):
            print(f"\n{'='*50}")
            print(f"Processing dashboard {i+1}/{len(dashboard_urls)}: {url}")
            print(f"{'='*50}")
            
            result = self.capture_dashboard(url)
            results.append(result)
        
        return results