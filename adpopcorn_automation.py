import asyncio
import os
import schedule
import time
from datetime import datetime, timedelta
from playwright.async_api import async_playwright
import logging

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('adpopcorn_automation.log'),
        logging.StreamHandler()
    ]
)

class AdpopcornAutomation:
    def __init__(self):
        self.login_url = "https://operation.adpopcorn.com/login"
        self.upload_url = "https://script.google.com/a/macros/adpopcorn.com/s/AKfycbwBnBzDDDihtCU37CXa7XCboCh1J9_DLCWgWPNvZEbGtBMcErUQH9kMFW8JJgF7vyrP/exec"
        self.email = "alex.nam@adpopcorn.com"
        self.password = "js97860909!"
        self.download_dir = os.path.join(os.getcwd(), "downloads")
        
        # 다운로드 폴더 생성
        os.makedirs(self.download_dir, exist_ok=True)
    
    def get_yesterday_date(self):
        """어제 날짜를 YYYY-MM-DD 형식으로 반환"""
        yesterday = datetime.now() - timedelta(days=1)
        return yesterday.strftime("%Y-%m-%d")
    
    async def run_automation(self):
        """메인 자동화 프로세스 실행"""
        try:
            logging.info("애드팝콘 리포트 자동화 시작")
            
            async with async_playwright() as p:
                # 브라우저 설정
                browser = await p.chromium.launch(
                    headless=True,  # 백그라운드 실행
                    downloads_path=self.download_dir
                )
                
                context = await browser.new_context(
                    accept_downloads=True
                )
                
                page = await context.new_page()
                
                # 1단계: 로그인
                await self.login(page)
                
                # 2단계: 리포트 다운로드
                downloaded_file = await self.download_report(page)
                
                # 3단계: 파일 업로드
                await self.upload_file(page, downloaded_file)
                
                await browser.close()
                
            logging.info("자동화 프로세스 완료")
            
        except Exception as e:
            logging.error(f"자동화 프로세스 오류: {str(e)}")
            raise
    
    async def login(self, page):
        """애드팝콘 사이트 로그인"""
        logging.info("로그인 시작")
        
        await page.goto(self.login_url)
        await page.wait_for_load_state('networkidle')
        
        # 이메일 입력
        await page.fill('input[placeholder="이메일"], textbox[name="이메일"]', self.email)
        
        # 비밀번호 입력
        await page.fill('input[type="password"], textbox[name="비밀번호"]', self.password)
        
        # 로그인 버튼 클릭
        await page.click('button:has-text("로그인")')
        
        # 로그인 완료 대기
        await page.wait_for_url("**/dashboard**")
        logging.info("로그인 완료")
    
    async def download_report(self, page):
        """리포트 파일 다운로드"""
        yesterday = self.get_yesterday_date()
        logging.info(f"리포트 다운로드 시작 - 날짜: {yesterday}")
        
        # 리포트 페이지로 이동 (어제 날짜)
        report_url = f"https://operation.adpopcorn.com/report/campaign?startDate={yesterday}&endDate={yesterday}&searchType=1"
        await page.goto(report_url)
        await page.wait_for_load_state('networkidle')
        
        # 데이터 로딩 대기
        await page.wait_for_timeout(5000)
        
        # 다운로드 시작
        async with page.expect_download() as download_info:
            await page.click('button:has-text("테이블 내보내기")')
        
        download = await download_info.value
        
        # 파일 저장
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"campaign_report_{yesterday}_{timestamp}.xlsx"
        filepath = os.path.join(self.download_dir, filename)
        
        await download.save_as(filepath)
        logging.info(f"파일 다운로드 완료: {filepath}")
        
        return filepath
    
    async def upload_file(self, page, file_path):
        """Google Apps Script에 파일 업로드"""
        yesterday = self.get_yesterday_date()
        logging.info(f"파일 업로드 시작: {file_path}")
        
        # 업로드 페이지로 이동
        await page.goto(self.upload_url)
        await page.wait_for_load_state('networkidle')
        
        # 팝업 닫기 (있는 경우)
        try:
            await page.click('button:has-text("닫기")', timeout=3000)
        except:
            pass
        
        # iframe 내부로 접근
        await page.wait_for_selector('iframe')
        iframe = page.frame_locator('iframe').nth(1)  # 두 번째 iframe
        
        # 파일 업로드
        await iframe.locator('text=엑셀 파일을 여기에 드래그하거나 클릭하세요').click()
        await page.set_input_files('input[type="file"]', file_path)
        
        # 업로드 완료 대기
        await page.wait_for_timeout(3000)
        
        # 어제 날짜 선택
        await iframe.locator(f'text=📅 {yesterday}').click()
        
        # 처리 시작
        await iframe.locator('button:has-text("선택된 1개 날짜 처리하기")').click()
        
        # 처리 완료 대기
        await iframe.locator('text=✅ 처리 완료!').wait_for(timeout=60000)
        
        logging.info("파일 업로드 및 처리 완료")
    
    def schedule_daily_run(self):
        """매일 오전 9시 실행 스케줄 설정"""
        schedule.every().day.at("09:00").do(self.run_scheduled_task)
        logging.info("스케줄 설정 완료: 매일 오전 9시 실행")
        
        while True:
            schedule.run_pending()
            time.sleep(60)  # 1분마다 확인
    
    def run_scheduled_task(self):
        """스케줄된 작업 실행"""
        try:
            asyncio.run(self.run_automation())
        except Exception as e:
            logging.error(f"스케줄된 작업 실행 중 오류: {str(e)}")

def main():
    """메인 실행 함수"""
    automation = AdpopcornAutomation()
    
    # 즉시 실행 (테스트용)
    if len(os.sys.argv) > 1 and os.sys.argv[1] == "--now":
        asyncio.run(automation.run_automation())
    else:
        # 스케줄 실행
        print("애드팝콘 자동화 스케줄러 시작")
        print("매일 오전 9시에 자동 실행됩니다.")
        print("종료하려면 Ctrl+C를 누르세요.")
        automation.schedule_daily_run()

if __name__ == "__main__":
    main()
