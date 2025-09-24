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
    """Smoke test for /healthz endpoint with standardized retry mechanism"""
    url = urljoin(STAGING_URL, '/healthz')
    
    MAX_RETRIES = 2  # Standardized to 2 retries
    RETRY_INTERVAL = 120  # Standardized to 120s intervals
    
    for attempt in range(MAX_RETRIES + 1):  # +1 for initial attempt
        try:
            response = requests.get(url, timeout=60)
            response.raise_for_status()
            data = response.json()
            
            assert response.status_code == 200
            assert data['status'] == 'healthy'
            assert 'metrics' in data and 'health_up' in data['metrics']
            assert data['metrics']['health_up'] == 1
            break
        except (requests.exceptions.RequestException, AssertionError) as e:
            if attempt == MAX_RETRIES:
                raise
            print(f"Retry attempt {attempt + 1} after {RETRY_INTERVAL}s...")
            time.sleep(RETRY_INTERVAL)
            assert data['status'] == 'ok'
            return
            
        except (requests.RequestException, AssertionError) as e:
            if attempt == MAX_RETRIES - 1:
                raise
            time.sleep(RETRY_DELAY)