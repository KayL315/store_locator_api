from datetime import datetime, timedelta
from fastapi import HTTPException, Request


MAX_REQUESTS_PER_MINUTE = 10
MAX_REQUESTS_PER_HOUR = 100


class InMemoryRateLimiter:
    def __init__(self):
        self.requests = {}

    def check_rate_limit(self, ip: str):
        now = datetime.now()

        if ip not in self.requests:
            self.requests[ip] = []

        one_hour_ago = now - timedelta(hours=1)
        self.requests[ip] = [
            request_time
            for request_time in self.requests[ip]
            if request_time > one_hour_ago
        ]

        one_minute_ago = now - timedelta(minutes=1)

        requests_last_minute = [
            request_time
            for request_time in self.requests[ip]
            if request_time > one_minute_ago
        ]

        requests_last_hour = self.requests[ip]

        if len(requests_last_minute) >= MAX_REQUESTS_PER_MINUTE:
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded: maximum 10 requests per minute.",
                headers={
                    "Retry-After": "60",
                    "X-RateLimit-Limit": str(MAX_REQUESTS_PER_MINUTE),
                    "X-RateLimit-Remaining": "0",
                },
            )

        if len(requests_last_hour) >= MAX_REQUESTS_PER_HOUR:
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded: maximum 100 requests per hour.",
                headers={
                    "Retry-After": "3600",
                    "X-RateLimit-Limit": str(MAX_REQUESTS_PER_HOUR),
                    "X-RateLimit-Remaining": "0",
                },
            )

        self.requests[ip].append(now)


rate_limiter = InMemoryRateLimiter()


def rate_limit_dependency(request: Request):
    client_ip = request.client.host
    rate_limiter.check_rate_limit(client_ip)