#!/bin/bash
# g4f Startup Script
# Custom startup script for g4f with configurable options

set -euo pipefail

# Default configuration
DEFAULT_PORT=8081
DEFAULT_HOST="0.0.0.0"
DEFAULT_WORKERS=1
DEFAULT_LOG_LEVEL="info"

# Configuration from environment variables
PORT="${G4F_PORT:-$DEFAULT_PORT}"
HOST="${G4F_HOST:-$DEFAULT_HOST}"
WORKERS="${G4F_WORKERS:-$DEFAULT_WORKERS}"
LOG_LEVEL="${G4F_LOG_LEVEL:-$DEFAULT_LOG_LEVEL}"
ENV_FILE="${G4F_ENV_FILE:-/home/OnlyAProgrammer/g4f-app/.env}"

# Venv path
VENV_PATH="/home/OnlyAProgrammer/g4f-app/venv"
PYTHON="${VENV_PATH}/bin/python"

# PID file for process management
PID_FILE="/tmp/g4f.pid"

# Function to load environment variables
load_env() {
    if [[ -f "$ENV_FILE" ]]; then
        echo "Loading environment from $ENV_FILE"
        set -a
        source "$ENV_FILE"
        set +a
    else
        echo "Warning: Environment file $ENV_FILE not found"
    fi
}

# Function to check if process is running
is_running() {
    if [[ -f "$PID_FILE" ]]; then
        local pid=$(cat "$PID_FILE" 2>/dev/null)
        if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
            echo "$pid"
            return 0
        fi
    fi
    return 1
}

# Function to start g4f
start_g4f() {
    local existing_pid=$(is_running)
    if [[ -n "$existing_pid" ]]; then
        echo "g4f is already running with PID $existing_pid"
        return 1
    fi

    echo "Starting g4f on $HOST:$PORT with $WORKERS worker(s)..."

    # Activate venv and run g4f
    cd /home/OnlyAProgrammer/g4f-app
    source "$VENV_PATH/bin/activate"

    # Run g4f in background
    nohup "$PYTHON" -m g4f \
        --host "$HOST" \
        --port "$PORT" \
        --workers "$WORKERS" \
        --log-level "$LOG_LEVEL" \
        > /tmp/g4f.log 2>&1 &

    local pid=$!
    echo "$pid" > "$PID_FILE"

    # Wait a moment and verify it's running
    sleep 2
    if kill -0 "$pid" 2>/dev/null; then
        echo "g4f started successfully with PID $pid"
        echo "Logs: /tmp/g4f.log"
        return 0
    else
        echo "Failed to start g4f"
        rm -f "$PID_FILE"
        return 1
    fi
}

# Function to stop g4f
stop_g4f() {
    local pid=$(is_running)
    if [[ -z "$pid" ]]; then
        echo "g4f is not running"
        return 1
    fi

    echo "Stopping g4f (PID: $pid)..."
    kill "$pid"

    # Wait for graceful shutdown
    local count=0
    while kill -0 "$pid" 2>/dev/null && [[ $count -lt 10 ]]; do
        sleep 1
        ((count++))
    done

    if kill -0 "$pid" 2>/dev/null; then
        echo "Force killing g4f..."
        kill -9 "$pid"
    fi

    rm -f "$PID_FILE"
    echo "g4f stopped"
}

# Function to restart g4f
restart_g4f() {
    stop_g4f
    sleep 2
    start_g4f
}

# Function to show status
status_g4f() {
    local pid=$(is_running)
    if [[ -n "$pid" ]]; then
        echo "g4f is running (PID: $pid)"
        echo "Port: $PORT"
        echo "Host: $HOST"
        echo "Workers: $WORKERS"
        return 0
    else
        echo "g4f is not running"
        return 1
    fi
}

# Function to show logs
logs_g4f() {
    if [[ -f /tmp/g4f.log ]]; then
        tail -f /tmp/g4f.log
    else
        echo "No log file found"
    fi
}

# Main command handling
case "${1:-start}" in
    start)
        load_env
        start_g4f
        ;;
    stop)
        stop_g4f
        ;;
    restart)
        load_env
        restart_g4f
        ;;
    status)
        status_g4f
        ;;
    logs)
        logs_g4f
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|logs}"
        echo "Environment variables:"
        echo "  G4F_PORT        - Port to listen on (default: $DEFAULT_PORT)"
        echo "  G4F_HOST        - Host to bind to (default: $DEFAULT_HOST)"
        echo "  G4F_WORKERS     - Number of workers (default: $DEFAULT_WORKERS)"
        echo "  G4F_LOG_LEVEL   - Log level (default: $DEFAULT_LOG_LEVEL)"
        echo "  G4F_ENV_FILE    - Path to .env file (default: $ENV_FILE)"
        exit 1
        ;;
esac