import os
import pytest
import requests
from urllib.parse import urljoin
import time
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
if Path('.env').exists():
    load_dotenv()

STAGING_URL = os.getenv('STAGING_URL', 'http://localhost:8000')
MAX_RETRIES = 3
RETRY_DELAY = 2

def test_healthz_endpoint():
    """Smoke test for /healthz endpoint"""
    url = urljoin(STAGING_URL, '/healthz')
    
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(url, timeout=60)
            response.raise_for_status()
            data = response.json()  # Get JSON immediately after raise_for_status
            
            assert response.status_code == 200
            assert data['status'] == 'healthy'
            break
        except (requests.exceptions.RequestException, AssertionError) as e:
            if attempt == MAX_RETRIES - 1:
                raise
            time.sleep(RETRY_DELAY)
            assert data['status'] == 'ok'
            return
            
        except (requests.RequestException, AssertionError) as e:
            if attempt == MAX_RETRIES - 1:
                raise
            time.sleep(RETRY_DELAY)