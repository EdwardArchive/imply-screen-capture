import asyncio
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, List
from urllib.parse import urlparse
from playwright.async_api import async_playwright, Page


class DashboardCapture:
    def __init__(self, base_url: str, username: str, password: str, config: Optional[Dict] = None):
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.password = password
        self.config = {
            'screenshot_dir': './screenshots',
            'format': 'png',
            'full_page': True,
            'wait_time': 5000,
            'viewport': {'width': 1920, 'height': 1080},
            'headless': True,  # 리눅스 서버용 기본값 True
            **(config or {})
        }
        self._browser = None
        self._context = None
        self._page = None
        self._playwright = None
        self._is_logged_in = False
    
    def ensure_screenshot_dir(self):
        """스크린샷 디렉토리가 존재하는지 확인하고 없으면 생성합니다."""
        Path(self.config['screenshot_dir']).mkdir(parents=True, exist_ok=True)
    
    def extract_dashboard_name(self, url: str) -> str:
        """URL에서 대시보드 이름을 추출합니다."""
        # URL의 마지막 부분을 대시보드 이름으로 사용
        parsed = urlparse(url)
        path_parts = parsed.path.rstrip('/').split('/')
        
        # 마지막 부분이 대시보드 이름
        if path_parts:
            dashboard_name = path_parts[-1]
            # 특수문자를 언더스코어로 변경
            return "".join(c if c.isalnum() or c in '-_' else '_' for c in dashboard_name)
        
        return "dashboard"
    
    def generate_filename(self, dashboard_name: str) -> str:
        """스크린샷 파일명을 생성합니다."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return f"{dashboard_name}_{timestamp}.{self.config['format']}"
    
    async def wait_for_dashboard_load(self, page: Page):
        """대시보드가 완전히 로드될 때까지 대기합니다."""
        try:
            # 먼저 대시보드 컨테이너가 나타날 때까지 대기
            await page.wait_for_selector(
                '.dashboard-container, .pivot-container, .chart-container, .pivot-application',
                timeout=15000,
                state='visible'
            )
            
            # 네트워크가 안정될 때까지 대기 (최대 5초)
            try:
                await page.wait_for_load_state('networkidle', timeout=5000)
            except:
                pass  # 타임아웃이 나도 계속 진행
            
            # 추가로 잠시 대기 (렌더링 완료를 위해)
            await page.wait_for_timeout(1000)
            
            print("✅ Dashboard loaded")
            
        except Exception as e:
            print(f"⚠️  Dashboard load check warning: {e}")
            # 에러가 나도 최소한의 대기 시간은 확보
            await page.wait_for_timeout(2000)
    
    async def login(self, page: Page) -> bool:
        """로그인을 수행합니다."""
        if self._is_logged_in:
            return True
            
        try:
            # 메인 페이지로 이동 (로그인 페이지)
            print(f"Navigating to: {self.base_url}")
            await page.goto(self.base_url, wait_until='domcontentloaded')
            
            # 이미 로그인되어 있는지 확인
            if 'pivot' in page.url:
                print("✅ Already logged in")
                self._is_logged_in = True
                return True
            
            # 로그인 폼 찾기 및 입력
            # Imply 특정 로그인 필드 선택자들
            username_selectors = [
                'input.text-input.immutable-text-input.name',  # Imply 특정 선택자
                'input.name',
                'input[name="username"]',
                'input[name="email"]',
                'input[type="email"]',
                'input[id="username"]'
            ]
            
            password_selectors = [
                'input.text-input.immutable-text-input.pass',  # Imply 특정 선택자
                'input.pass',
                'input[name="password"]',
                'input[type="password"]',
                'input[id="password"]'
            ]
            
            # 사용자명 입력
            username_input = None
            for selector in username_selectors:
                try:
                    username_input = await page.wait_for_selector(selector, timeout=2000)
                    if username_input:
                        await username_input.click()
                        await username_input.fill('')
                        await username_input.type(self.username)
                        print(f"✅ Username entered")
                        break
                except:
                    continue
            
            if not username_input:
                print("❌ Could not find username input field")
                return False
            
            # 비밀번호 입력
            password_input = None
            for selector in password_selectors:
                try:
                    password_input = await page.query_selector(selector)
                    if password_input:
                        await password_input.click()
                        await password_input.fill('')
                        await password_input.type(self.password)
                        print(f"✅ Password entered")
                        break
                except:
                    continue
            
            if not password_input:
                print("❌ Could not find password input field")
                return False
            
            # 로그인 제출 (Enter 키 사용)
            print("⏎ Submitting login...")
            await password_input.press('Enter')
            
            # 로그인 완료 대기
            await page.wait_for_timeout(2000)
            
            # 로그인 성공 확인
            try:
                await page.wait_for_url('**/pivot/**', timeout=5000)
                print("✅ Login successful")
                self._is_logged_in = True
                return True
            except:
                if 'pivot' in page.url:
                    print("✅ Login successful")
                    self._is_logged_in = True
                    return True
                else:
                    print("❌ Login failed")
                    return False
                    
        except Exception as e:
            print(f"❌ Login error: {e}")
            return False
    
    async def capture_single_dashboard(self, page: Page, dashboard_url: str) -> Dict:
        """단일 대시보드를 캡처합니다."""
        dashboard_name = self.extract_dashboard_name(dashboard_url)
        
        try:
            # 대시보드로 이동
            print(f"Navigating to dashboard: {dashboard_url}")
            await page.goto(dashboard_url, wait_until='domcontentloaded')
            
            # 대시보드 로드 대기
            await self.wait_for_dashboard_load(page)
            
            # 스크린샷 저장
            filename = self.generate_filename(dashboard_name)
            filepath = os.path.join(self.config['screenshot_dir'], filename)
            
            await page.screenshot(
                path=filepath,
                full_page=self.config['full_page'],
                type=self.config['format']
            )
            
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
    
    async def initialize_browser(self):
        """브라우저를 초기화합니다."""
        if not self._browser:
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(
                headless=self.config['headless'],
                args=['--disable-blink-features=AutomationControlled']
            )
            self._context = await self._browser.new_context(
                viewport=self.config['viewport'],
                ignore_https_errors=True
            )
            self._page = await self._context.new_page()
    
    async def close_browser(self):
        """브라우저를 종료합니다."""
        try:
            if self._page:
                await self._page.close()
                self._page = None
            if self._context:
                await self._context.close()
                self._context = None
            if self._browser:
                await self._browser.close()
                self._browser = None
            if self._playwright:
                await self._playwright.stop()
                self._playwright = None
        except Exception as e:
            print(f"Warning during browser cleanup: {e}")
        finally:
            self._is_logged_in = False
    
    async def capture_dashboard(self, dashboard_url: str) -> Dict:
        """단일 대시보드를 캡처합니다 (로그인 포함)."""
        self.ensure_screenshot_dir()
        
        await self.initialize_browser()
        
        try:
            # 로그인 (필요한 경우)
            if not self._is_logged_in:
                login_success = await self.login(self._page)
                if not login_success:
                    return {
                        'success': False,
                        'dashboard_name': self.extract_dashboard_name(dashboard_url),
                        'dashboard_url': dashboard_url,
                        'error': 'Login failed'
                    }
            
            # 대시보드 캡처
            result = await self.capture_single_dashboard(self._page, dashboard_url)
            return result
            
        finally:
            # 단일 캡처의 경우 브라우저 종료
            await self.close_browser()
    
    async def capture_multiple_dashboards(self, dashboard_urls: List[str]) -> List[Dict]:
        """여러 대시보드를 순차적으로 캡처합니다."""
        self.ensure_screenshot_dir()
        results = []
        
        await self.initialize_browser()
        
        try:
            # 한 번만 로그인
            login_success = await self.login(self._page)
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
                
                result = await self.capture_single_dashboard(self._page, url)
                results.append(result)
                
                # 다음 대시보드 전에 잠시 대기 (마지막이 아닌 경우)
                if i < len(dashboard_urls) - 1:
                    await asyncio.sleep(1)
            
            return results
            
        finally:
            # 모든 캡처 완료 후 브라우저 종료
            await self.close_browser()
    
    def capture_dashboard_sync(self, dashboard_url: str) -> Dict:
        """동기적으로 대시보드를 캡처합니다."""
        if os.name == 'nt':  # Windows
            # Windows에서 ProactorEventLoop 문제 해결
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(self.capture_dashboard(dashboard_url))
            finally:
                loop.close()
        else:
            return asyncio.run(self.capture_dashboard(dashboard_url))
    
    def capture_multiple_dashboards_sync(self, dashboard_urls: List[str]) -> List[Dict]:
        """동기적으로 여러 대시보드를 캡처합니다."""
        if os.name == 'nt':  # Windows
            # Windows에서 ProactorEventLoop 문제 해결
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(self.capture_multiple_dashboards(dashboard_urls))
            finally:
                loop.close()
        else:
            return asyncio.run(self.capture_multiple_dashboards(dashboard_urls))