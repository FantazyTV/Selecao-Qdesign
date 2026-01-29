"""
Prometheus Metrics - Comprehensive observability for Co-Scientist Service.

Provides detailed metrics for:
- Request counting and latency
- Agent execution tracking
- Knowledge graph operations
- LLM API usage and costs
- Workflow success/failure rates
"""

from prometheus_client import Counter, Histogram, Gauge, Summary, Info
import time
from contextlib import contextmanager
from functools import wraps


# ============================================================================
# REQUEST METRICS
# ============================================================================

REQUESTS = Counter(
    "co_scientist_requests_total",
    "Total HTTP requests received",
    ["endpoint", "method", "status"]
)

LATENCY = Histogram(
    "co_scientist_request_latency_seconds",
    "Request latency in seconds",
    ["endpoint"],
    buckets=[0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 120.0]
)

ACTIVE_REQUESTS = Gauge(
    "co_scientist_active_requests",
    "Number of currently active requests",
    ["endpoint"]
)


# ============================================================================
# WORKFLOW METRICS
# ============================================================================

WORKFLOW_RUNS = Counter(
    "co_scientist_workflow_runs_total",
    "Total workflow executions",
    ["status", "exploration_mode"]
)

WORKFLOW_DURATION = Histogram(
    "co_scientist_workflow_duration_seconds",
    "Workflow execution duration",
    ["status"],
    buckets=[5.0, 15.0, 30.0, 60.0, 120.0, 300.0, 600.0]
)

WORKFLOW_ITERATIONS = Histogram(
    "co_scientist_workflow_iterations",
    "Number of critique-revise iterations per workflow",
    buckets=[1, 2, 3, 4, 5]
)

ACTIVE_WORKFLOWS = Gauge(
    "co_scientist_active_workflows",
    "Number of currently running workflows"
)


# ============================================================================
# AGENT METRICS
# ============================================================================

AGENT_CALLS = Counter(
    "co_scientist_agent_calls_total",
    "Total agent invocations",
    ["agent_name", "status"]
)

AGENT_DURATION = Histogram(
    "co_scientist_agent_duration_seconds",
    "Agent execution duration",
    ["agent_name"],
    buckets=[1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 120.0]
)

AGENT_CONFIDENCE = Summary(
    "co_scientist_agent_confidence",
    "Agent output confidence scores",
    ["agent_name"]
)

CRITIC_DECISIONS = Counter(
    "co_scientist_critic_decisions_total",
    "Critic agent decisions",
    ["decision"]
)


# ============================================================================
# KNOWLEDGE GRAPH METRICS
# ============================================================================

KG_LOAD_TIME = Histogram(
    "co_scientist_kg_load_seconds",
    "Knowledge graph loading time",
    buckets=[0.1, 0.5, 1.0, 2.5, 5.0, 10.0]
)

KG_SIZE = Gauge(
    "co_scientist_kg_size",
    "Knowledge graph size",
    ["dimension"]
)

KG_PATH_FINDING = Histogram(
    "co_scientist_kg_path_finding_seconds",
    "Path finding operation duration",
    ["strategy"],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0]
)

SUBGRAPH_EXTRACTION = Counter(
    "co_scientist_subgraph_extractions_total",
    "Number of subgraph extractions",
    ["strategy", "success"]
)


# ============================================================================
# LLM METRICS
# ============================================================================

LLM_CALLS = Counter(
    "co_scientist_llm_calls_total",
    "Total LLM API calls",
    ["provider", "model", "status"]
)

LLM_LATENCY = Histogram(
    "co_scientist_llm_latency_seconds",
    "LLM API response latency",
    ["provider", "model"],
    buckets=[1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 120.0]
)

LLM_TOKENS = Counter(
    "co_scientist_llm_tokens_total",
    "Total tokens used",
    ["provider", "model", "type"]
)

LLM_RETRIES = Counter(
    "co_scientist_llm_retries_total",
    "LLM API retry attempts",
    ["provider", "reason"]
)

LLM_CACHE_HITS = Counter(
    "co_scientist_llm_cache_hits_total",
    "LLM response cache hits"
)

LLM_CACHE_MISSES = Counter(
    "co_scientist_llm_cache_misses_total",
    "LLM response cache misses"
)


# ============================================================================
# SYSTEM METRICS
# ============================================================================

BUILD_INFO = Info(
    "co_scientist_build",
    "Build information"
)

UPTIME = Gauge(
    "co_scientist_uptime_seconds",
    "Service uptime in seconds"
)

CACHE_SIZE = Gauge(
    "co_scientist_cache_size_bytes",
    "Cache size in bytes",
    ["cache_type"]
)

CACHE_ENTRIES = Gauge(
    "co_scientist_cache_entries",
    "Number of cache entries",
    ["cache_type"]
)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

_start_time = time.time()


def initialize_metrics():
    """Initialize static metrics like build info."""
    BUILD_INFO.info({
        "version": "2.0.0",
        "framework": "SciAgents",
        "python_version": "3.12"
    })


def update_uptime():
    """Update the uptime gauge."""
    UPTIME.set(time.time() - _start_time)


@contextmanager
def track_request(endpoint: str):
    """Context manager to track request metrics."""
    ACTIVE_REQUESTS.labels(endpoint=endpoint).inc()
    start = time.time()
    status = "success"
    try:
        yield
    except Exception:
        status = "error"
        raise
    finally:
        duration = time.time() - start
        LATENCY.labels(endpoint=endpoint).observe(duration)
        REQUESTS.labels(endpoint=endpoint, method="POST", status=status).inc()
        ACTIVE_REQUESTS.labels(endpoint=endpoint).dec()


@contextmanager
def track_workflow(exploration_mode: str = "balanced"):
    """Context manager to track workflow metrics."""
    ACTIVE_WORKFLOWS.inc()
    start = time.time()
    status = "success"
    try:
        yield
    except Exception:
        status = "error"
        raise
    finally:
        duration = time.time() - start
        WORKFLOW_DURATION.labels(status=status).observe(duration)
        WORKFLOW_RUNS.labels(status=status, exploration_mode=exploration_mode).inc()
        ACTIVE_WORKFLOWS.dec()


@contextmanager
def track_agent(agent_name: str):
    """Context manager to track agent execution."""
    start = time.time()
    status = "success"
    try:
        yield
    except Exception:
        status = "error"
        raise
    finally:
        duration = time.time() - start
        AGENT_DURATION.labels(agent_name=agent_name).observe(duration)
        AGENT_CALLS.labels(agent_name=agent_name, status=status).inc()


def track_llm_call(provider: str, model: str, latency: float, 
                   tokens_in: int = 0, tokens_out: int = 0, 
                   status: str = "success"):
    """Record LLM API call metrics."""
    LLM_CALLS.labels(provider=provider, model=model, status=status).inc()
    LLM_LATENCY.labels(provider=provider, model=model).observe(latency)
    if tokens_in > 0:
        LLM_TOKENS.labels(provider=provider, model=model, type="input").inc(tokens_in)
    if tokens_out > 0:
        LLM_TOKENS.labels(provider=provider, model=model, type="output").inc(tokens_out)


def track_kg_loaded(nodes: int, edges: int, load_time: float):
    """Record knowledge graph loading metrics."""
    KG_LOAD_TIME.observe(load_time)
    KG_SIZE.labels(dimension="nodes").set(nodes)
    KG_SIZE.labels(dimension="edges").set(edges)


def track_critic_decision(decision: str):
    """Record critic decision."""
    CRITIC_DECISIONS.labels(decision=decision).inc()


def track_agent_confidence(agent_name: str, confidence: float):
    """Record agent confidence score."""
    AGENT_CONFIDENCE.labels(agent_name=agent_name).observe(confidence)


def track_path_finding(strategy: str, duration: float, success: bool):
    """Record path finding metrics."""
    KG_PATH_FINDING.labels(strategy=strategy).observe(duration)
    SUBGRAPH_EXTRACTION.labels(
        strategy=strategy, 
        success="true" if success else "false"
    ).inc()


def update_cache_metrics(cache_type: str, entries: int, size_bytes: int):
    """Update cache metrics."""
    CACHE_ENTRIES.labels(cache_type=cache_type).set(entries)
    CACHE_SIZE.labels(cache_type=cache_type).set(size_bytes)


def metrics_middleware(func):
    """Decorator to add metrics tracking to async functions."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        endpoint = func.__name__
        with track_request(endpoint):
            return await func(*args, **kwargs)
    return wrapper


# Initialize on import
initialize_metrics()
