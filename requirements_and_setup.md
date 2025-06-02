# 애드팝콘 리포트 자동화 설치 및 실행 가이드

## 📋 필요한 패키지 (requirements.txt)

```
playwright==1.40.0
schedule==1.2.0
```

## 🚀 설치 방법

### 1. Python 환경 설정
```bash
# 가상환경 생성 (권장)
python -m venv adpopcorn_automation
source adpopcorn_automation/bin/activate  # Linux/Mac
# 또는
adpopcorn_automation\Scripts\activate     # Windows

# 패키지 설치
pip install -r requirements.txt

# Playwright 브라우저 설치
playwright install chromium
```

### 2. 폴더 구조
```
adpopcorn_automation/
├── adpopcorn_automation.py    # 메인 스크립트
├── requirements.txt           # 패키지 목록
├── downloads/                 # 다운로드 폴더 (자동 생성)
└── adpopcorn_automation.log   # 로그 파일 (자동 생성)
```

## 🏃‍♂️ 실행 방법

### 1. 즉시 실행 (테스트용)
```bash
python adpopcorn_automation.py --now
```

### 2. 스케줄 실행 (매일 오전 9시)
```bash
python adpopcorn_automation.py
```

### 3. 백그라운드 실행 (Linux/Mac)
```bash
nohup python adpopcorn_automation.py > automation.out 2>&1 &
```

### 4. Windows 서비스로 실행
Task Scheduler를 사용하여 등록:
1. Windows 검색에서 "작업 스케줄러" 실행
2. "기본 작업 만들기" 클릭
3. 작업명: "애드팝콘 자동화"
4. 트리거: "매일" 선택, 시간: 09:00
5. 작업: 스크립트 경로 설정

## ⚙️ 설정 변경

### 로그인 정보 변경
```python
# adpopcorn_automation.py 파일에서 수정
self.email = "your_email@adpopcorn.com"
self.password = "your_password"
```

### 실행 시간 변경
```python
# 오전 8시로 변경하려면
schedule.every().day.at("08:00").do(self.run_scheduled_task)

# 여러 시간대 실행
schedule.every().day.at("09:00").do(self.run_scheduled_task)
schedule.every().day.at("18:00").do(self.run_scheduled_task)
```

### 날짜 범위 변경
```python
def get_date_range(self):
    """최근 3일 데이터를 가져오려면"""
    end_date = datetime.now() - timedelta(days=1)
    start_date = end_date - timedelta(days=2)
    return start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")
```

## 📊 로그 모니터링

### 실시간 로그 확인
```bash
tail -f adpopcorn_automation.log
```

### 로그 파일 예시
```
2025-06-02 09:00:01 - INFO - 애드팝콘 리포트 자동화 시작
2025-06-02 09:00:05 - INFO - 로그인 시작
2025-06-02 09:00:10 - INFO - 로그인 완료
2025-06-02 09:00:15 - INFO - 리포트 다운로드 시작 - 날짜: 2025-06-01
2025-06-02 09:00:25 - INFO - 파일 다운로드 완료: downloads/campaign_report_2025-06-01_20250602_090025.xlsx
2025-06-02 09:00:30 - INFO - 파일 업로드 시작: downloads/campaign_report_2025-06-01_20250602_090025.xlsx
2025-06-02 09:00:45 - INFO - 파일 업로드 및 처리 완료
2025-06-02 09:00:46 - INFO - 자동화 프로세스 완료
```

## 🛠️ 추가 기능

### 이메일 알림 추가
```python
import smtplib
from email.mime.text import MIMEText

def send_notification(self, message):
    """완료 알림 이메일 발송"""
    msg = MIMEText(message)
    msg['Subject'] = '애드팝콘 자동화 완료'
    msg['From'] = 'automation@company.com'
    msg['To'] = 'admin@company.com'
    
    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()
        server.login('your_email', 'your_password')
        server.send_message(msg)
```

### 에러 재시도 로직
```python
import time
from functools import wraps

def retry(max_attempts=3, delay=5):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_attempts - 1:
                        raise
                    logging.warning(f"시도 {attempt + 1} 실패: {e}. {delay}초 후 재시도...")
                    time.sleep(delay)
            return wrapper
    return decorator
```

## 🔧 문제 해결

### 브라우저 실행 오류
```bash
# Chromium 재설치
playwright install chromium --force
```

### 권한 오류 (Linux)
```bash
# 실행 권한 부여
chmod +x adpopcorn_automation.py
```

### 메모리 부족
```python
# 브라우저 옵션에 추가
browser = await p.chromium.launch(
    headless=True,
    args=['--no-sandbox', '--disable-dev-shm-usage']
)
```

## 📈 모니터링 대시보드

### Grafana + InfluxDB 연동 (고급)
```python
from influxdb import InfluxDBClient

def log_metrics(self, execution_time, success=True):
    """메트릭 로깅"""
    client = InfluxDBClient('localhost', 8086, 'user', 'pass', 'automation')
    
    json_body = [{
        "measurement": "automation_runs",
        "tags": {"success": success},
        "fields": {"execution_time": execution_time}
    }]
    
    client.write_points(json_body)
```
