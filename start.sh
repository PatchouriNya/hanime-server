#!/bin/sh

# Color definitions
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'

print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

handle_error() {
    print_error "$1 failed, exit code: $2"
    exit $2
}

show_banner() {
    echo -e "${GREEN}"
    echo "****************************************************"
    echo "*                                                  *"
    echo "*             HAnime Server Boot                   *"
    echo "*                                                  *"
    echo "****************************************************"
    echo -e "${NC}"
    echo -e "${CYAN}Version: 1.0.0${NC}"
    echo -e "${CYAN}Boot Time: $(date '+%Y-%m-%d %H:%M:%S')${NC}"
    echo ""
}

start_nginx() {
    print_step "Starting Nginx..."
    if nginx; then
        print_info "Nginx started successfully"
        if command -v hostname &> /dev/null; then
            HOST_IP=$(hostname -I 2>/dev/null || hostname -i | awk '{print $1}')
            echo -e "\n${CYAN}Access URLs:${NC}"
            echo -e "  ${BOLD}Local:${NC} http://localhost:7788"
            echo -e "  ${BOLD}Network:${NC} http://${HOST_IP}:7788"
            echo ""
        fi
    else
        handle_error "Nginx start" $?
    fi
}

start_backend() {
    print_step "Starting Backend..."
    cd /app/backend || handle_error "Change to backend directory" $?

    print_info "Initializing backend..."
    echo -e "  ${BOLD}Working Dir:${NC} $(pwd)"
    echo -e "  ${BOLD}Python Version:${NC} $(python3 --version)"
    echo ""

    python3 -c "import uvicorn; uvicorn.run('main:app', host='0.0.0.0', port=8000, workers=1, limit_max_requests=1000, timeout_keep_alive=15)" || handle_error "Python backend start" $?
}

main() {
    show_banner
    start_nginx
    start_backend

    print_error "All services stopped unexpectedly. Please check logs."
}

main
