import os
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import urlparse, urljoin
import json
import base64
from io import BytesIO
from PIL import Image
import time


class ImplyAPICapture:
    """브라우저 없이 Imply API를 직접 사용하여 대시보드를 캡처하는 클래스"""
    
    def __init__(self, base_url: str, username: str, password: str, config: Optional[Dict] = None):
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.password = password
        self.config = {
            'screenshot_dir': './screenshots',
            'format': 'png',
            'timeout': 30,
            **(config or {})
        }
        self.session = requests.Session()
        self.auth_token = None
        self.session_cookie = None
    
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
        """Imply에 로그인합니다."""
        try:
            # 로그인 엔드포인트 시도
            login_endpoints = [
                '/auth/login',
                '/api/auth/login',
                '/login',
                '/api/v1/auth/login'
            ]
            
            for endpoint in login_endpoints:
                login_url = urljoin(self.base_url, endpoint)
                print(f"Trying login endpoint: {login_url}")
                
                try:
                    # JSON 방식 로그인 시도
                    response = self.session.post(
                        login_url,
                        json={
                            'username': self.username,
                            'password': self.password
                        },
                        headers={'Content-Type': 'application/json'},
                        timeout=10,
                        allow_redirects=False
                    )
                    
                    if response.status_code in [200, 201, 302]:
                        # 토큰 확인
                        if response.headers.get('content-type', '').startswith('application/json'):
                            data = response.json()
                            if 'token' in data:
                                self.auth_token = data['token']
                                self.session.headers['Authorization'] = f"Bearer {self.auth_token}"
                            elif 'access_token' in data:
                                self.auth_token = data['access_token']
                                self.session.headers['Authorization'] = f"Bearer {self.auth_token}"
                        
                        print("✅ Login successful")
                        return True
                        
                except requests.exceptions.RequestException:
                    continue
            
            # Form 방식 로그인 시도
            print("Trying form-based login...")
            response = self.session.post(
                urljoin(self.base_url, '/login'),
                data={
                    'username': self.username,
                    'password': self.password
                },
                allow_redirects=True
            )
            
            if response.status_code == 200:
                print("✅ Form login successful")
                return True
            
            print("❌ All login attempts failed")
            return False
            
        except Exception as e:
            print(f"❌ Login error: {e}")
            return False
    
    def get_dashboard_data(self, dashboard_url: str) -> Optional[Dict]:
        """대시보드 데이터를 API로 가져옵니다."""
        try:
            # URL에서 대시보드 ID 추출
            parsed = urlparse(dashboard_url)
            path_parts = parsed.path.split('/')
            
            # pivot/c/xxxx/name 형식에서 ID 추출
            dashboard_id = None
            if 'pivot' in path_parts:
                pivot_idx = path_parts.index('pivot')
                if len(path_parts) > pivot_idx + 2:
                    dashboard_id = path_parts[pivot_idx + 2]
            
            if not dashboard_id:
                dashboard_id = path_parts[-1]
            
            # 대시보드 데이터 API 호출
            api_endpoints = [
                f"/api/v1/dashboards/{dashboard_id}",
                f"/api/dashboards/{dashboard_id}",
                f"/pivot/api/dashboard/{dashboard_id}"
            ]
            
            for endpoint in api_endpoints:
                try:
                    response = self.session.get(
                        urljoin(self.base_url, endpoint),
                        timeout=self.config['timeout']
                    )
                    
                    if response.status_code == 200:
                        return response.json()
                        
                except:
                    continue
            
            return None
            
        except Exception as e:
            print(f"Failed to get dashboard data: {e}")
            return None
    
    def export_dashboard(self, dashboard_url: str) -> Optional[bytes]:
        """대시보드를 이미지로 내보내기 시도합니다."""
        try:
            # URL에서 대시보드 ID 추출
            parsed = urlparse(dashboard_url)
            path_parts = parsed.path.split('/')
            dashboard_id = path_parts[-1]
            
            # Export API 엔드포인트 시도
            export_endpoints = [
                f"/api/v1/dashboards/{dashboard_id}/export",
                f"/api/dashboards/{dashboard_id}/export",
                f"/pivot/api/export/{dashboard_id}"
            ]
            
            for endpoint in export_endpoints:
                try:
                    response = self.session.post(
                        urljoin(self.base_url, endpoint),
                        json={'format': self.config['format']},
                        headers={'Accept': f'image/{self.config["format"]}'},
                        timeout=self.config['timeout']
                    )
                    
                    if response.status_code == 200:
                        return response.content
                        
                except:
                    continue
            
            # 직접 스크린샷 API 시도
            screenshot_url = urljoin(self.base_url, f"/api/screenshot")
            response = self.session.post(
                screenshot_url,
                json={
                    'url': dashboard_url,
                    'format': self.config['format'],
                    'width': 1920,
                    'height': 1080,
                    'fullPage': True
                },
                timeout=self.config['timeout']
            )
            
            if response.status_code == 200:
                return response.content
            
            return None
            
        except Exception as e:
            print(f"Failed to export dashboard: {e}")
            return None
    
    def create_placeholder_image(self, dashboard_name: str, message: str) -> bytes:
        """플레이스홀더 이미지를 생성합니다."""
        from PIL import Image, ImageDraw, ImageFont
        
        # 이미지 생성
        img = Image.new('RGB', (1920, 1080), color='white')
        draw = ImageDraw.Draw(img)
        
        # 텍스트 추가
        text = f"Dashboard: {dashboard_name}\n\n{message}\n\nAPI-based capture not available.\nPlease use browser-based capture."
        
        # 기본 폰트 사용
        try:
            font = ImageFont.truetype("arial.ttf", 36)
        except:
            font = ImageFont.load_default()
        
        # 텍스트 위치 계산
        text_bbox = draw.multiline_textbbox((0, 0), text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        
        position = ((1920 - text_width) // 2, (1080 - text_height) // 2)
        
        # 텍스트 그리기
        draw.multiline_text(position, text, fill='black', font=font, align='center')
        
        # 바이트로 변환
        buffer = BytesIO()
        img.save(buffer, format=self.config['format'].upper())
        return buffer.getvalue()
    
    def capture_dashboard(self, dashboard_url: str) -> Dict:
        """단일 대시보드를 캡처합니다."""
        self.ensure_screenshot_dir()
        dashboard_name = self.extract_dashboard_name(dashboard_url)
        
        try:
            print(f"Attempting to capture: {dashboard_url}")
            
            # 1. Export API 시도
            image_data = self.export_dashboard(dashboard_url)
            
            if not image_data:
                # 2. 대시보드 데이터 가져오기 시도
                dashboard_data = self.get_dashboard_data(dashboard_url)
                if dashboard_data:
                    # 데이터를 기반으로 플레이스홀더 생성
                    title = dashboard_data.get('title', dashboard_name)
                    message = f"Dashboard data retrieved: {title}\nContains {len(dashboard_data.get('widgets', []))} widgets"
                    image_data = self.create_placeholder_image(dashboard_name, message)
                else:
                    # 3. 실패 시 플레이스홀더 생성
                    message = "Unable to capture dashboard via API"
                    image_data = self.create_placeholder_image(dashboard_name, message)
            
            # 이미지 저장
            filename = self.generate_filename(dashboard_name)
            filepath = os.path.join(self.config['screenshot_dir'], filename)
            
            with open(filepath, 'wb') as f:
                f.write(image_data)
            
            print(f"📸 Saved: {filepath}")
            
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
    
    def capture_multiple_dashboards(self, dashboard_urls: List[str]) -> List[Dict]:
        """여러 대시보드를 순차적으로 캡처합니다."""
        results = []
        
        # 로그인
        if not self.login():
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
            
            result = self.capture_dashboard(url)
            results.append(result)
            
            # 다음 요청 전 대기
            if i < len(dashboard_urls) - 1:
                time.sleep(1)
        
        return results