import http from 'k6/http';
import { sleep } from 'k6';
import { check, group } from 'k6';

export let options = {
  vus: 50,
  duration: '2m',
  thresholds: {
    http_req_duration: ['p(95)<250'],  // 95% of requests must complete within 250ms
    http_req_failed: ['rate<0.01'],    // Error rate must be below 1%
  },
};

const BASE_URL = __ENV.SERVICE_URL || 'http://localhost:8000';

export default function () {
  group('basic-endpoints', function () {
    // Health check endpoint
    let healthRes = http.get(`${BASE_URL}/health`);
    check(healthRes, {
      'health-status-2xx': (r) => r.status >= 200 && r.status < 300,
      'health-response-time': (r) => r.timings.duration < 200,
    });

    // Ping endpoint
    let pingRes = http.get(`${BASE_URL}/ping`);
    check(pingRes, {
      'ping-status-2xx': (r) => r.status >= 200 && r.status < 300,
      'ping-response-time': (r) => r.timings.duration < 200,
      'ping-response-valid': (r) => r.json().message === 'pong',
    });

    sleep(1);
  });
}