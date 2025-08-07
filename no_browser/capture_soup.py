import os
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, List
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
import imgkit
import pdfkit
import urllib3

# SSL 경고 비활성화
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class DashboardCaptureSoup:
    def __init__(self, base_url: str, username: str, password: str, config: Optional[Dict] = None):
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.password = password
        self.config = {
            'screenshot_dir': './screenshots',
            'format': 'png',
            'wait_time': 5000,
            'viewport': {'width': 1920, 'height': 1080},
            'wkhtmltoimage_path': None,  # Path to wkhtmltoimage executable
            'timeout': 30,  # Request timeout in seconds
            'no_login_dashboard_url': None,  # 로그인 없이 접근 가능한 대시보드 URL
            **(config or {})
        }
        self.session = requests.Session()
        # 세션 설정
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ko-KR,ko;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        self.session.verify = False  # SSL 인증서 검증 비활성화
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
    
    def generate_filename(self, dashboard_name: str) -> str:
        """스크린샷 파일명을 생성합니다."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return f"{dashboard_name}_{timestamp}.{self.config['format']}"
    
    def login(self) -> bool:
        """로그인을 수행합니다."""
        if self._is_logged_in:
            return True
            
        try:
            # 메인 페이지로 이동 (로그인 페이지)
            print(f"Navigating to: {self.base_url}")
            response = self.session.get(
                self.base_url, 
                timeout=self.config['timeout'],
                allow_redirects=True
            )
            
            # 이미 로그인되어 있는지 확인
            if 'pivot' in response.url:
                print("✅ Already logged in")
                self._is_logged_in = True
                return True
            
            # HTML 파싱
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 로그인 폼 찾기
            login_form = soup.find('form')
            if not login_form:
                # API 엔드포인트로 직접 로그인 시도
                login_url = urljoin(self.base_url, '/auth/login')
                login_data = {
                    'username': self.username,
                    'password': self.password
                }
                
                print("⏎ Submitting login...")
                response = self.session.post(
                    login_url, 
                    json=login_data, 
                    timeout=self.config['timeout'],
                    allow_redirects=True
                )
                
                if response.status_code == 200:
                    print("✅ Login successful")
                    self._is_logged_in = True
                    return True
                else:
                    # Form 데이터로 재시도
                    response = self.session.post(
                        login_url, 
                        data=login_data, 
                        timeout=self.config['timeout'],
                        allow_redirects=True
                    )
                    if response.status_code == 200:
                        print("✅ Login successful")
                        self._is_logged_in = True
                        return True
            else:
                # 폼 액션 URL 가져오기
                action = login_form.get('action', '/auth/login')
                login_url = urljoin(self.base_url, action)
                
                # 폼 데이터 준비
                form_data = {}
                
                # 숨겨진 필드들 포함
                for input_field in login_form.find_all('input'):
                    name = input_field.get('name')
                    value = input_field.get('value', '')
                    if name:
                        form_data[name] = value
                
                # 사용자명과 비밀번호 설정
                username_fields = ['username', 'name', 'email', 'user']
                password_fields = ['password', 'pass', 'pwd']
                
                for field in username_fields:
                    if field in form_data or login_form.find('input', {'name': field}):
                        form_data[field] = self.username
                        break
                
                for field in password_fields:
                    if field in form_data or login_form.find('input', {'name': field}):
                        form_data[field] = self.password
                        break
                
                print("⏎ Submitting login...")
                response = self.session.post(
                    login_url, 
                    data=form_data, 
                    timeout=self.config['timeout'],
                    allow_redirects=True
                )
                
                if response.status_code == 200 and 'pivot' in response.url:
                    print("✅ Login successful")
                    self._is_logged_in = True
                    return True
            
            print("❌ Login failed")
            return False
                    
        except Exception as e:
            print(f"❌ Login error: {e}")
            return False
    
    def capture_single_dashboard(self, dashboard_url: str) -> Dict:
        """단일 대시보드를 캡처합니다."""
        dashboard_name = self.extract_dashboard_name(dashboard_url)
        
        try:
            # 대시보드 페이지 가져오기
            print(f"Fetching dashboard: {dashboard_url}")
            response = self.session.get(
                dashboard_url, 
                timeout=self.config['timeout'],
                allow_redirects=True
            )
            
            if response.status_code != 200:
                raise Exception(f"Failed to fetch dashboard: HTTP {response.status_code}")
            
            # HTML 파싱
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 스타일시트와 스크립트 URL을 절대 경로로 변환
            for link in soup.find_all('link', href=True):
                if not link['href'].startswith(('http://', 'https://', '//')):
                    link['href'] = urljoin(dashboard_url, link['href'])
            
            for script in soup.find_all('script', src=True):
                if not script['src'].startswith(('http://', 'https://', '//')):
                    script['src'] = urljoin(dashboard_url, script['src'])
            
            for img in soup.find_all('img', src=True):
                if not img['src'].startswith(('http://', 'https://', '//')):
                    img['src'] = urljoin(dashboard_url, img['src'])
            
            # 추가 스타일 삽입 (대시보드가 제대로 렌더링되도록)
            style_tag = soup.new_tag('style')
            style_tag.string = """
                body {
                    width: """ + str(self.config['viewport']['width']) + """px;
                    height: """ + str(self.config['viewport']['height']) + """px;
                    margin: 0;
                    padding: 0;
                }
                .dashboard-container, .pivot-container {
                    width: 100%;
                    height: 100%;
                }
            """
            soup.head.append(style_tag)
            
            # HTML을 이미지로 변환
            html_content = str(soup)
            filename = self.generate_filename(dashboard_name)
            filepath = os.path.join(self.config['screenshot_dir'], filename)
            
            # imgkit 옵션 설정
            options = {
                'format': self.config['format'],
                'width': self.config['viewport']['width'],
                'height': self.config['viewport']['height'],
                'javascript-delay': self.config['wait_time'],
                'no-stop-slow-scripts': '',
                'enable-javascript': ''
            }
            
            # wkhtmltoimage 경로가 설정되어 있으면 사용
            config = None
            if self.config.get('wkhtmltoimage_path'):
                config = imgkit.config(wkhtmltoimage=self.config['wkhtmltoimage_path'])
            
            # HTML을 이미지로 변환
            imgkit.from_string(html_content, filepath, options=options, config=config)
            
            print(f"📸 Screenshot saved: {filepath}")
            
            return {
                'success': True,
                'filepath': filepath,
                'filename': filename,
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
        """단일 대시보드를 캡처합니다 (로그인 포함)."""
        self.ensure_screenshot_dir()
        
        # no_login_dashboard_url이 설정되어 있으면 로그인 없이 직접 캡처
        if self.config.get('no_login_dashboard_url'):
            print("Using no_login_dashboard_url - skipping login")
            return self.capture_single_dashboard(self.config['no_login_dashboard_url'])
        
        # 로그인 (필요한 경우)
        if not self._is_logged_in:
            login_success = self.login()
            if not login_success:
                return {
                    'success': False,
                    'dashboard_name': self.extract_dashboard_name(dashboard_url),
                    'dashboard_url': dashboard_url,
                    'error': 'Login failed'
                }
        
        # 대시보드 캡처
        result = self.capture_single_dashboard(dashboard_url)
        return result
    
    def capture_multiple_dashboards(self, dashboard_urls: List[str]) -> List[Dict]:
        """여러 대시보드를 순차적으로 캡처합니다."""
        self.ensure_screenshot_dir()
        results = []
        
        # no_login_dashboard_url이 설정되어 있으면 로그인 없이 직접 캡처
        if self.config.get('no_login_dashboard_url'):
            print("Using no_login_dashboard_url - skipping login")
            for i, _ in enumerate(dashboard_urls):
                print(f"\n{'='*50}")
                print(f"Processing dashboard {i+1}/{len(dashboard_urls)}: {self.config['no_login_dashboard_url']}")
                print(f"{'='*50}")
                
                result = self.capture_single_dashboard(self.config['no_login_dashboard_url'])
                results.append(result)
            return results
        
        # 한 번만 로그인
        login_success = self.login()
        if not login_success:
            # 로그인 실패 시 모든 대시보드에 대해 실패 반환
            for url in dashboard_urls:
                results.append({
                    'success': False,
                    'dashboard_name': self.extract_dashboard_name(url),
                    'dashboard_url': url,
                    'error': 'Login failed'
                })
            return results
        
        # 각 대시보드 캡처
        for i, url in enumerate(dashboard_urls):
            print(f"\n{'='*50}")
            print(f"Processing dashboard {i+1}/{len(dashboard_urls)}: {url}")
            print(f"{'='*50}")
            
            result = self.capture_single_dashboard(url)
            results.append(result)
        
        return results