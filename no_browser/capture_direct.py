import os
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import urlparse
import base64
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import time


class DirectDashboardCapture:
    """브라우저 없이 대시보드 URL에 직접 접근하여 캡처를 시도하는 클래스"""
    
    def __init__(self, session_cookie: Optional[str] = None, auth_token: Optional[str] = None, config: Optional[Dict] = None):
        self.config = {
            'screenshot_dir': './screenshots',
            'format': 'png',
            'timeout': 30,
            **(config or {})
        }
        self.session = requests.Session()
        
        # 제공된 인증 정보 설정
        if session_cookie:
            self.session.cookies.set('session', session_cookie)
        if auth_token:
            self.session.headers['Authorization'] = f"Bearer {auth_token}"
    
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
    
    def create_info_image(self, dashboard_name: str, info: Dict) -> bytes:
        """대시보드 정보를 담은 이미지를 생성합니다."""
        # 이미지 생성
        img = Image.new('RGB', (1920, 1080), color='#f5f5f5')
        draw = ImageDraw.Draw(img)
        
        # 헤더 배경
        draw.rectangle([(0, 0), (1920, 120)], fill='#2c3e50')
        
        # 제목
        title = f"Dashboard: {dashboard_name}"
        try:
            title_font = ImageFont.truetype("arial.ttf", 48)
            info_font = ImageFont.truetype("arial.ttf", 24)
        except:
            title_font = ImageFont.load_default()
            info_font = ImageFont.load_default()
        
        draw.text((50, 30), title, fill='white', font=title_font)
        
        # 정보 표시
        y_offset = 180
        for key, value in info.items():
            text = f"{key}: {value}"
            draw.text((50, y_offset), text, fill='#34495e', font=info_font)
            y_offset += 40
        
        # 경고 메시지
        warning = "⚠️ Browser-based capture is required for actual dashboard screenshots"
        draw.text((50, 900), warning, fill='#e74c3c', font=info_font)
        
        # 바이트로 변환
        buffer = BytesIO()
        img.save(buffer, format=self.config['format'].upper())
        return buffer.getvalue()
    
    def try_direct_access(self, dashboard_url: str) -> Dict:
        """대시보드 URL에 직접 접근을 시도합니다."""
        try:
            # 대시보드 페이지 요청
            response = self.session.get(
                dashboard_url,
                timeout=self.config['timeout'],
                allow_redirects=True
            )
            
            # 응답 분석
            info = {
                'URL': dashboard_url,
                'Status Code': response.status_code,
                'Content Type': response.headers.get('content-type', 'Unknown'),
                'Content Length': len(response.content),
                'Final URL': response.url
            }
            
            # HTML 내용 확인
            if 'text/html' in response.headers.get('content-type', ''):
                content = response.text.lower()
                if 'login' in content or 'sign in' in content:
                    info['Status'] = 'Redirected to login page'
                elif 'dashboard' in content or 'pivot' in content:
                    info['Status'] = 'Dashboard HTML retrieved (rendering required)'
                else:
                    info['Status'] = 'Unknown HTML content'
            else:
                info['Status'] = 'Non-HTML response'
            
            return info
            
        except requests.exceptions.Timeout:
            return {'Status': 'Request timeout', 'Error': 'Connection timed out'}
        except requests.exceptions.ConnectionError:
            return {'Status': 'Connection failed', 'Error': 'Unable to connect to server'}
        except Exception as e:
            return {'Status': 'Error', 'Error': str(e)}
    
    def capture_dashboard(self, dashboard_url: str) -> Dict:
        """단일 대시보드를 캡처합니다."""
        self.ensure_screenshot_dir()
        dashboard_name = self.extract_dashboard_name(dashboard_url)
        
        try:
            print(f"Attempting direct access to: {dashboard_url}")
            
            # 직접 접근 시도
            access_info = self.try_direct_access(dashboard_url)
            
            # 정보 이미지 생성
            image_data = self.create_info_image(dashboard_name, access_info)
            
            # 이미지 저장
            filename = self.generate_filename(dashboard_name)
            filepath = os.path.join(self.config['screenshot_dir'], filename)
            
            with open(filepath, 'wb') as f:
                f.write(image_data)
            
            print(f"📸 Info saved: {filepath}")
            
            return {
                'success': True,
                'filepath': filepath,
                'filename': filename,
                'dashboard_name': dashboard_name,
                'dashboard_url': dashboard_url,
                'info': access_info
            }
            
        except Exception as e:
            print(f"❌ Failed to process dashboard: {e}")
            return {
                'success': False,
                'dashboard_name': dashboard_name,
                'dashboard_url': dashboard_url,
                'error': str(e)
            }
    
    def capture_multiple_dashboards(self, dashboard_urls: List[str]) -> List[Dict]:
        """여러 대시보드를 순차적으로 처리합니다."""
        results = []
        
        for i, url in enumerate(dashboard_urls):
            print(f"\n{'='*50}")
            print(f"Processing dashboard {i+1}/{len(dashboard_urls)}")
            print(f"{'='*50}")
            
            result = self.capture_dashboard(url)
            results.append(result)
            
            # 다음 요청 전 대기
            if i < len(dashboard_urls) - 1:
                time.sleep(1)
        
        return results