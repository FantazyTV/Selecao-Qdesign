#!/bin/bash
# Co-Scientist Service Startup Script

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/co_scientist_venv"
LOG_FILE="$SCRIPT_DIR/server.log"
PID_FILE="$SCRIPT_DIR/server.pid"
HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8000}"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_venv() {
    if [ ! -d "$VENV_DIR" ]; then
        log_error "Virtual environment not found at $VENV_DIR"
        log_info "Run: uv venv --python 3.12 co_scientist_venv"
        exit 1
    fi
}

check_env_file() {
    if [ ! -f "$SCRIPT_DIR/.env" ]; then
        log_warn ".env file not found"
        log_info "Using default configuration"
    fi
}

stop_server() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            log_info "Stopping server (PID: $PID)..."
            kill "$PID"
            rm "$PID_FILE"
            log_info "Server stopped"
        else
            log_warn "PID file exists but process not running"
            rm "$PID_FILE"
        fi
    else
        log_info "Server not running (no PID file)"
    fi
}

start_server() {
    check_venv
    check_env_file
    
    # Stop existing server
    stop_server
    
    log_info "Starting Co-Scientist Service..."
    log_info "Host: $HOST"
    log_info "Port: $PORT"
    log_info "Log file: $LOG_FILE"
    
    # Start server in background
    nohup "$VENV_DIR/bin/python" -m uvicorn src.main:app \
        --host "$HOST" \
        --port "$PORT" \
        --reload \
        > "$LOG_FILE" 2>&1 &
    
    SERVER_PID=$!
    echo "$SERVER_PID" > "$PID_FILE"
    
    # Wait for server to start
    log_info "Waiting for server to start..."
    sleep 3
    
    # Check if server is running
    if ps -p "$SERVER_PID" > /dev/null 2>&1; then
        log_info "Server started successfully (PID: $SERVER_PID)"
        log_info "API Documentation: http://localhost:$PORT/docs"
        log_info "OpenAPI Spec: http://localhost:$PORT/openapi.json"
        log_info ""
        log_info "Tail logs with: tail -f $LOG_FILE"
    else
        log_error "Server failed to start. Check $LOG_FILE for errors"
        exit 1
    fi
}

status_server() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            log_info "Server is running (PID: $PID)"
            log_info "Listening on http://localhost:$PORT"
        else
            log_warn "PID file exists but process not running"
        fi
    else
        log_info "Server is not running"
    fi
}

show_logs() {
    if [ -f "$LOG_FILE" ]; then
        tail -f "$LOG_FILE"
    else
        log_error "Log file not found: $LOG_FILE"
        exit 1
    fi
}

# Main script
case "${1:-start}" in
    start)
        start_server
        ;;
    stop)
        stop_server
        ;;
    restart)
        stop_server
        start_server
        ;;
    status)
        status_server
        ;;
    logs)
        show_logs
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|logs}"
        echo ""
        echo "Commands:"
        echo "  start   - Start the server"
        echo "  stop    - Stop the server"
        echo "  restart - Restart the server"
        echo "  status  - Check server status"
        echo "  logs    - Tail server logs"
        exit 1
        ;;
esac
