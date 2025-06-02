# 서버 배포 및 운영 가이드

## 🕘 Cron 스케줄링 (Linux/Mac)

### 1. Cron 설정
```bash
# crontab 편집
crontab -e

# 매일 오전 9시 실행 (cron 표기법)
0 9 * * * /path/to/python /path/to/adpopcorn_automation.py --now

# 예시: 절대 경로 사용
0 9 * * * /home/user/adpopcorn_automation/bin/python /home/user/adpopcorn_automation/adpopcorn_automation.py --now >> /home/user/automation.log 2>&1
```

### 2. Cron 스크립트 래퍼 생성
```bash
#!/bin/bash
# automation_wrapper.sh

# 작업 디렉토리 설정
cd /home/user/adpopcorn_automation

# 가상환경 활성화
source bin/activate

# Python 스크립트 실행
python adpopcorn_automation.py --now

# 실행 결과 로깅
echo "$(date): Automation completed" >> automation.log
```

```bash
# 실행 권한 부여
chmod +x automation_wrapper.sh

# crontab에 등록
0 9 * * * /home/user/automation_wrapper.sh
```

## 🐳 Docker 컨테이너화

### 1. Dockerfile
```dockerfile
FROM python:3.11-slim

# 시스템 패키지 설치
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# 작업 디렉토리 설정
WORKDIR /app

# Python 패키지 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Playwright 브라우저 설치
RUN playwright install chromium
RUN playwright install-deps chromium

# 소스 코드 복사
COPY adpopcorn_automation.py .

# 다운로드 디렉토리 생성
RUN mkdir -p /app/downloads

# 실행
CMD ["python", "adpopcorn_automation.py"]
```

### 2. docker-compose.yml
```yaml
version: '3.8'

services:
  adpopcorn-automation:
    build: .
    container_name: adpopcorn-automation
    volumes:
      - ./downloads:/app/downloads
      - ./logs:/app/logs
    environment:
      - TZ=Asia/Seoul
    restart: unless-stopped
    
  # 스케줄러 (선택사항)
  scheduler:
    image: mcuadros/ofelia:latest
    container_name: automation-scheduler
    depends_on:
      - adpopcorn-automation
    command: daemon --docker
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
    labels:
      ofelia.job-run.automation.schedule: "0 0 9 * * *"  # 매일 9시
      ofelia.job-run.automation.container: "adpopcorn-automation"
```

### 3. Docker 실행
```bash
# 이미지 빌드 및 실행
docker-compose up -d

# 즉시 실행 (테스트)
docker-compose exec adpopcorn-automation python adpopcorn_automation.py --now

# 로그 확인
docker-compose logs -f adpopcorn-automation
```

## 📊 시스템 모니터링

### 1. Systemd 서비스 (Linux)
```ini
# /etc/systemd/system/adpopcorn-automation.service

[Unit]
Description=Adpopcorn Report Automation
After=network.target

[Service]
Type=simple
User=automation
WorkingDirectory=/home/automation/adpopcorn_automation
ExecStart=/home/automation/adpopcorn_automation/bin/python adpopcorn_automation.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# 서비스 등록 및 시작
sudo systemctl daemon-reload
sudo systemctl enable adpopcorn-automation
sudo systemctl start adpopcorn-automation

# 상태 확인
sudo systemctl status adpopcorn-automation
```

### 2. 헬스체크 스크립트
```python
#!/usr/bin/env python3
# health_check.py

import os
import sys
from datetime import datetime, timedelta

def check_recent_execution():
    """최근 실행 확인"""
    log_file = "adpopcorn_automation.log"
    
    if not os.path.exists(log_file):
        return False
        
    # 최근 24시간 내 성공 로그 확인
    cutoff_time = datetime.now() - timedelta(hours=24)
    
    with open(log_file, 'r') as f:
        for line in reversed(f.readlines()):
            if "자동화 프로세스 완료" in line:
                # 로그 시간 파싱
                log_time_str = line.split(' - ')[0]
                log_time = datetime.strptime(log_time_str, '%Y-%m-%d %H:%M:%S,%f')
                
                if log_time > cutoff_time:
                    return True
    
    return False

def check_download_files():
    """다운로드 파일 확인"""
    download_dir = "downloads"
    
    if not os.path.exists(download_dir):
        return False
    
    # 최근 24시간 내 파일 확인
    cutoff_time = datetime.now() - timedelta(hours=24)
    
    for filename in os.listdir(download_dir):
        filepath = os.path.join(download_dir, filename)
        file_time = datetime.fromtimestamp(os.path.getmtime(filepath))
        
        if file_time > cutoff_time:
            return True
    
    return False

if __name__ == "__main__":
    checks = [
        ("Recent execution", check_recent_execution()),
        ("Download files", check_download_files())
    ]
    
    all_passed = True
    for check_name, result in checks:
        status = "PASS" if result else "FAIL"
        print(f"{check_name}: {status}")
        if not result:
            all_passed = False
    
    sys.exit(0 if all_passed else 1)
```

### 3. Slack 알림 통합
```python
import requests
import json

class SlackNotifier:
    def __init__(self, webhook_url):
        self.webhook_url = webhook_url
    
    def send_message(self, message, color="good"):
        """Slack 메시지 전송"""
        payload = {
            "attachments": [{
                "color": color,
                "fields": [{
                    "title": "애드팝콘 자동화",
                    "value": message,
                    "short": False
                }],
                "footer": "Automation Bot",
                "ts": int(time.time())
            }]
        }
        
        response = requests.post(
            self.webhook_url,
            data=json.dumps(payload),
            headers={'Content-Type': 'application/json'}
        )
        
        return response.status_code == 200

# 사용법
notifier = SlackNotifier("https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK")

# 성공 알림
notifier.send_message("✅ 리포트 자동화 완료", "good")

# 실패 알림  
notifier.send_message("❌ 자동화 실행 실패", "danger")
```

## 🔐 보안 고려사항

### 1. 환경변수 사용
```python
import os

class SecureAdpopcornAutomation(AdpopcornAutomation):
    def __init__(self):
        super().__init__()
        self.email = os.getenv("ADPOPCORN_EMAIL")
        self.password = os.getenv("ADPOPCORN_PASSWORD")
        
        if not self.email or not self.password:
            raise ValueError("환경변수 ADPOPCORN_EMAIL, ADPOPCORN_PASSWORD 설정 필요")
```

```bash
# 환경변수 설정
export ADPOPCORN_EMAIL="alex.nam@adpopcorn.com"
export ADPOPCORN_PASSWORD="js97860909!"

# 또는 .env 파일 사용
echo "ADPOPCORN_EMAIL=alex.nam@adpopcorn.com" > .env
echo "ADPOPCORN_PASSWORD=js97860909!" >> .env
```

### 2. 암호화된 설정 파일
```python
from cryptography.fernet import Fernet
import json

def encrypt_config(config_data, key):
    """설정 데이터 암호화"""
    f = Fernet(key)
    encrypted_data = f.encrypt(json.dumps(config_data).encode())
    return encrypted_data

def decrypt_config(encrypted_data, key):
    """설정 데이터 복호화"""
    f = Fernet(key)
    decrypted_data = f.decrypt(encrypted_data)
    return json.loads(decrypted_data.decode())

# 키 생성 (한 번만 실행)
key = Fernet.generate_key()
with open('secret.key', 'wb') as key_file:
    key_file.write(key)
```

## 📈 성능 최적화

### 1. 병렬 처리
```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

async def parallel_automation(date_list):
    """여러 날짜 병렬 처리"""
    tasks = []
    
    for date in date_list:
        task = asyncio.create_task(process_single_date(date))
        tasks.append(task)
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return results
```

### 2. 캐싱
```python
from functools import lru_cache
import pickle

@lru_cache(maxsize=128)
def get_cached_data(date):
    """캐시된 데이터 조회"""
    cache_file = f"cache_{date}.pkl"
    
    if os.path.exists(cache_file):
        with open(cache_file, 'rb') as f:
            return pickle.load(f)
    
    return None
```

이제 완전한 자동화 시스템이 구성되었습니다! 매일 오전 9시에 어제 날짜의 리포트를 자동으로 다운로드하고 업로드하는 시스템이 안정적으로 운영될 수 있습니다.
