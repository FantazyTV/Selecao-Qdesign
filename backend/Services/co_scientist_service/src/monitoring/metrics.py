from prometheus_client import Counter, Histogram


REQUESTS = Counter("co_scientist_requests", "Total requests", ["endpoint"])
LATENCY = Histogram("co_scientist_latency_seconds", "Request latency", ["endpoint"])
