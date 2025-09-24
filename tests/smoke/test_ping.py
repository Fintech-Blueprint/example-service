import os
import pytest
import requests
from urllib.parse import urljoin
import time

STAGING_URL = os.environ['STAGING_URL']
MAX_RETRIES = 3
RETRY_DELAY = 2

def test_healthz_endpoint():
    """Smoke test for /healthz endpoint"""
    url = urljoin(STAGING_URL, '/healthz')
    
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(url, timeout=60)
            response.raise_for_status()
            
            assert response.status_code == 200
            data = response.json()
            assert data['status'] == 'ok'
            return
            
        except (requests.RequestException, AssertionError) as e:
            if attempt == MAX_RETRIES - 1:
                raise
            time.sleep(RETRY_DELAY)