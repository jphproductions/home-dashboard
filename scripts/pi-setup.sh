#!/bin/bash

# ============================================
# Home Dashboard - Raspberry Pi Setup Script
# ============================================
# Automated installation script for deploying
# Home Dashboard on Raspberry Pi 5
# ============================================

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script configuration
REPO_URL="https://github.com/jphproductions/home-dashboard.git"
INSTALL_DIR="$HOME/home-dashboard"
REPO_DIR="$INSTALL_DIR"

# ============================================
# Utility Functions
# ============================================

print_header() {
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

prompt_input() {
    local prompt="$1"
    local default="$2"
    local result

    if [ -n "$default" ]; then
        read -p "$(echo -e ${BLUE}$prompt${NC} [${GREEN}$default${NC}]: )" result
        echo "${result:-$default}"
    else
        read -p "$(echo -e ${BLUE}$prompt${NC}: )" result
        echo "$result"
    fi
}

prompt_secure() {
    local prompt="$1"
    local result
    read -sp "$(echo -e ${BLUE}$prompt${NC}: )" result
    echo ""
    echo "$result"
}

confirm() {
    local prompt="$1"
    local response
    read -p "$(echo -e ${YELLOW}$prompt${NC} [y/N]: )" response
    case "$response" in
        [yY][eE][sS]|[yY])
            return 0
            ;;
        *)
            return 1
            ;;
    esac
}

check_command() {
    if command -v "$1" &> /dev/null; then
        return 0
    else
        return 1
    fi
}

# ============================================
# Main Installation Steps
# ============================================

welcome_message() {
    clear
    print_header "Home Dashboard - Raspberry Pi Setup"
    echo ""
    echo "This script will install and configure the Home Dashboard"
    echo "on your Raspberry Pi 5 with the following steps:"
    echo ""
    echo "  1. Update system packages"
    echo "  2. Install Docker and Docker Compose"
    echo "  3. Install required packages (Chromium, utilities)"
    echo "  4. Clone/update repository"
    echo "  5. Configure environment variables"
    echo "  6. Set up systemd services"
    echo "  7. Configure kiosk mode"
    echo "  8. Disable screen blanking"
    echo ""
    print_warning "This script requires sudo privileges for some operations."
    echo ""

    if ! confirm "Do you want to continue?"; then
        print_info "Installation cancelled."
        exit 0
    fi
}

update_system() {
    print_header "Step 1: Updating System Packages"

    print_info "Updating package lists..."
    sudo apt update

    print_info "Upgrading installed packages..."
    sudo apt upgrade -y

    print_success "System updated successfully"
    echo ""
}

install_docker() {
    print_header "Step 2: Installing Docker"

    if check_command docker; then
        print_info "Docker is already installed"
        docker --version
    else
        print_info "Downloading and installing Docker..."
        curl -fsSL https://get.docker.com -o /tmp/get-docker.sh
        sudo sh /tmp/get-docker.sh
        rm /tmp/get-docker.sh

        print_success "Docker installed successfully"
    fi

    # Check if user is in docker group
    if ! groups "$USER" | grep -q docker; then
        print_info "Adding user to docker group..."
        sudo usermod -aG docker "$USER"
        print_success "Docker group added"
        print_info "Using 'sg docker' to activate group for this script (avoids logout/login)"
    fi

    # Verify Docker Compose
    if docker compose version &> /dev/null 2>&1; then
        print_success "Docker Compose is available"
        docker compose version
    elif sg docker -c "docker compose version" &> /dev/null 2>&1; then
        print_success "Docker Compose is available (via sg docker)"
        sg docker -c "docker compose version"
    else
        print_error "Docker Compose not found. Please install it manually."
        exit 1
    fi

    echo ""
}

install_packages() {
    print_header "Step 3: Installing Required Packages"

    print_info "Installing Chromium, unclutter, xdotool, and git..."
    sudo apt install -y chromium unclutter xdotool git

    print_success "Required packages installed"
    echo ""
}

setup_repository() {
    print_header "Step 4: Setting Up Repository"

    if [ -d "$REPO_DIR/.git" ]; then
        print_info "Repository already exists at $REPO_DIR"
        cd "$REPO_DIR"

        if confirm "Do you want to pull the latest changes?"; then
            print_info "Pulling latest changes..."
            git pull
            print_success "Repository updated"
        fi
    else
        print_info "Cloning repository to $REPO_DIR..."
        git clone "$REPO_URL" "$REPO_DIR"
        cd "$REPO_DIR"
        print_success "Repository cloned successfully"
    fi

    echo ""
}

generate_random_key() {
    openssl rand -base64 32 | tr -d "=+/" | cut -c1-32
}

configure_environment() {
    print_header "Step 5: Configuring Environment Variables"

    ENV_FILE="$REPO_DIR/.env"

    if [ -f "$ENV_FILE" ]; then
        print_warning "Environment file already exists: $ENV_FILE"
        if ! confirm "Do you want to reconfigure it?"; then
            print_info "Skipping environment configuration"
            echo ""
            return
        fi

        # Backup existing .env
        cp "$ENV_FILE" "$ENV_FILE.backup.$(date +%Y%m%d_%H%M%S)"
        print_info "Backup created"
    fi

    print_info "Please provide the following configuration values..."
    echo ""

    # Generate API key
    print_info "Generating secure API key..."
    DASHBOARD_API_KEY=$(generate_random_key)

    # API Configuration
    API_HOST=$(prompt_input "API Host" "0.0.0.0")
    API_PORT=$(prompt_input "API Port" "8000")
    API_BASE_URL=$(prompt_input "API Base URL" "http://localhost:$API_PORT")

    # TV Configuration
    echo ""
    print_info "TV Configuration (press Enter to skip if not using TV features)"
    TV_IP=$(prompt_input "TV IP Address" "")
    TV_SPOTIFY_DEVICE_ID=$(prompt_input "TV Spotify Device ID" "")

    # Weather Configuration
    echo ""
    print_info "Weather Configuration"
    WEATHER_API_KEY=$(prompt_input "OpenWeather API Key" "")
    WEATHER_LOCATION=$(prompt_input "Weather Location" "Amsterdam")
    WEATHER_LATITUDE=$(prompt_input "Weather Latitude" "52.3676")
    WEATHER_LONGITUDE=$(prompt_input "Weather Longitude" "4.9041")

    # Spotify Configuration
    echo ""
    print_info "Spotify Configuration"
    SPOTIFY_CLIENT_ID=$(prompt_input "Spotify Client ID" "")
    SPOTIFY_CLIENT_SECRET=$(prompt_input "Spotify Client Secret" "")
    SPOTIFY_REDIRECT_URI=$(prompt_input "Spotify Redirect URI" "http://localhost:$API_PORT/api/spotify/auth/callback")

    # IFTTT Configuration
    echo ""
    print_info "IFTTT Configuration (press Enter to skip if not using)"
    IFTTT_WEBHOOK_KEY=$(prompt_input "IFTTT Webhook Key" "placeholder-webhook-key")
    IFTTT_EVENT_NAME=$(prompt_input "IFTTT Event Name" "placeholder-event-name")

    # Security Configuration
    echo ""
    CORS_ORIGINS=$(prompt_input "CORS Origins (comma-separated)" "http://localhost:$API_PORT,http://$(hostname).local:$API_PORT")
    TRUSTED_HOSTS=$(prompt_input "Trusted Hosts (comma-separated)" "localhost,$(hostname).local,127.0.0.1")

    # Logging
    LOG_LEVEL=$(prompt_input "Log Level" "INFO")

    # Write .env file
    cat > "$ENV_FILE" << EOF
# API Configuration
API_HOST=$API_HOST
API_PORT=$API_PORT
API_BASE_URL=$API_BASE_URL
DASHBOARD_API_KEY=$DASHBOARD_API_KEY

# TV Configuration
TV_IP=$TV_IP
TV_SPOTIFY_DEVICE_ID=$TV_SPOTIFY_DEVICE_ID

# Weather Configuration
WEATHER_API_KEY=$WEATHER_API_KEY
WEATHER_LOCATION=$WEATHER_LOCATION
WEATHER_LATITUDE=$WEATHER_LATITUDE
WEATHER_LONGITUDE=$WEATHER_LONGITUDE

# Spotify Configuration
SPOTIFY_CLIENT_ID=$SPOTIFY_CLIENT_ID
SPOTIFY_CLIENT_SECRET=$SPOTIFY_CLIENT_SECRET
SPOTIFY_REDIRECT_URI=$SPOTIFY_REDIRECT_URI
SPOTIFY_REFRESH_TOKEN=

# IFTTT Configuration
IFTTT_WEBHOOK_KEY=$IFTTT_WEBHOOK_KEY
IFTTT_EVENT_NAME=$IFTTT_EVENT_NAME

# CORS and Security
CORS_ORIGINS=$CORS_ORIGINS
TRUSTED_HOSTS=$TRUSTED_HOSTS

# Logging
LOG_LEVEL=$LOG_LEVEL

# Optional: Proxy settings
HTTP_PROXY=
HTTPS_PROXY=
EOF

    print_success "Environment file created: $ENV_FILE"
    print_warning "Note: SPOTIFY_REFRESH_TOKEN is empty - you'll need to obtain it later"
    echo ""
}

start_docker_container() {
    print_header "Step 6: Starting Docker Container"

    cd "$REPO_DIR"

    # Check if .env file exists
    if [ ! -f ".env" ]; then
        print_error ".env file not found in $REPO_DIR"
        exit 1
    fi

    print_info "Building and starting Docker container..."
    # Use sg docker to activate docker group without sudo side effects
    if docker ps &> /dev/null 2>&1; then
        docker compose -f docker/docker-compose.yml up -d --build
    else
        print_info "Using 'sg docker' to run with docker group (no sudo needed)"
        sg docker -c "docker compose -f docker/docker-compose.yml up -d --build"
    fi

    print_info "Waiting for container to start..."
    sleep 5

    # Check container status - look for running containers
    if docker ps -a &> /dev/null 2>&1; then
        CONTAINER_CHECK=$(docker ps --filter "name=dashboard" --filter "status=running" --format "{{.Names}}" || true)
        CONTAINER_STATUS=$(docker ps -a --filter "name=dashboard" --format "{{.Names}} - {{.Status}}")
    else
        CONTAINER_CHECK=$(sg docker -c "docker ps --filter 'name=dashboard' --filter 'status=running' --format '{{.Names}}'" || true)
        CONTAINER_STATUS=$(sg docker -c "docker ps -a --filter 'name=dashboard' --format '{{.Names}} - {{.Status}}'")
    fi

    if [ -n "$CONTAINER_CHECK" ]; then
        print_success "Docker container is running"
        echo ""
        print_info "Container status:"
        echo "$CONTAINER_STATUS"
        echo ""
        print_info "Check logs: docker logs -f docker-dashboard-1"
    else
        print_error "Container failed to start or exited"
        echo ""
        print_info "Container status:"
        echo "$CONTAINER_STATUS"
        echo ""
        print_info "Container logs (last 30 lines):"
        if docker logs &> /dev/null 2>&1; then
            docker logs --tail 30 docker-dashboard-1 2>&1 || true
        else
            sg docker -c "docker logs --tail 30 docker-dashboard-1" 2>&1 || true
        fi
        echo ""
        print_info "To view full logs: sg docker -c 'docker logs docker-dashboard-1'"
        exit 1
    fi

    echo ""
}

setup_systemd_services() {
    print_header "Step 7: Setting Up Systemd Services"

    # Docker Dashboard Service
    print_info "Installing docker-dashboard.service..."
    sudo cp "$REPO_DIR/infra/systemd/docker-dashboard.service" /etc/systemd/system/

    # Update WorkingDirectory in service file to match installation directory
    sudo sed -i "s|WorkingDirectory=.*|WorkingDirectory=$REPO_DIR|g" /etc/systemd/system/docker-dashboard.service
    sudo sed -i "s|ExecStart=.*|ExecStart=/usr/bin/docker compose -f $REPO_DIR/docker/docker-compose.yml up|g" /etc/systemd/system/docker-dashboard.service
    sudo sed -i "s|ExecStop=.*|ExecStop=/usr/bin/docker compose -f $REPO_DIR/docker/docker-compose.yml down|g" /etc/systemd/system/docker-dashboard.service

    sudo systemctl daemon-reload
    sudo systemctl enable docker-dashboard.service
    print_success "docker-dashboard.service installed and enabled"

    # Chromium Kiosk Service
    print_info "Installing kiosk-chromium.service..."
    sudo cp "$REPO_DIR/infra/systemd/kiosk-chromium.service" /etc/systemd/system/

    # Update user in service file
    sudo sed -i "s|User=.*|User=$USER|g" /etc/systemd/system/kiosk-chromium.service

    sudo systemctl daemon-reload
    sudo systemctl enable kiosk-chromium.service
    print_success "kiosk-chromium.service installed and enabled"

    echo ""
}

configure_autologin() {
    print_header "Step 8: Configuring Auto-login"

    if confirm "Do you want to enable desktop auto-login for kiosk mode?"; then
        print_info "Configuring auto-login..."

        # Configure auto-login using raspi-config non-interactively
        sudo raspi-config nonint do_boot_behaviour B4

        print_success "Auto-login configured"
    else
        print_warning "Skipping auto-login configuration"
        print_info "You can enable it later with: sudo raspi-config"
    fi

    echo ""
}

disable_screen_blanking() {
    print_header "Step 9: Disabling Screen Blanking"

    # Configure LightDM
    print_info "Configuring LightDM..."
    if [ -f /etc/lightdm/lightdm.conf ]; then
        if ! grep -q "xserver-command=X -s 0 -dpms" /etc/lightdm/lightdm.conf; then
            sudo sed -i '/^\[Seat:\*\]/a xserver-command=X -s 0 -dpms' /etc/lightdm/lightdm.conf
            print_success "LightDM configured"
        else
            print_info "LightDM already configured"
        fi
    else
        print_warning "LightDM config not found, skipping"
    fi

    # Configure LXDE autostart
    print_info "Configuring LXDE autostart..."
    AUTOSTART_DIR="$HOME/.config/lxsession/LXDE-pi"
    AUTOSTART_FILE="$AUTOSTART_DIR/autostart"

    mkdir -p "$AUTOSTART_DIR"

    if [ ! -f "$AUTOSTART_FILE" ] || ! grep -q "xset s off" "$AUTOSTART_FILE"; then
        cat >> "$AUTOSTART_FILE" << 'EOF'
@xset s off
@xset -dpms
@xset s noblank
EOF
        print_success "LXDE autostart configured"
    else
        print_info "LXDE autostart already configured"
    fi

    echo ""
}

print_next_steps() {
    print_header "Installation Complete!"

    echo -e "${GREEN}✓ System setup completed successfully!${NC}"
    echo ""
    echo "Next steps:"
    echo ""
    echo "1. ${YELLOW}Get Spotify Refresh Token:${NC}"
    echo "   - Visit: http://$(hostname).local:8000/api/spotify/auth/login"
    echo "   - Authorize with Spotify"
    echo "   - Copy the refresh token"
    echo "   - Update .env: nano $REPO_DIR/.env"
    echo "   - Add: SPOTIFY_REFRESH_TOKEN=your_token_here"
    echo "   - Restart: docker compose -f $REPO_DIR/docker/docker-compose.yml restart"
    echo ""
    echo "2. ${YELLOW}Reboot your Raspberry Pi:${NC}"
    echo "   sudo reboot"
    echo ""
    echo "3. ${YELLOW}After reboot:${NC}"
    echo "   - Dashboard should auto-start in kiosk mode"
    echo "   - Access from other devices: http://$(hostname).local:8000"
    echo ""
    echo "${BLUE}Useful Commands:${NC}"
    echo "  View logs:          docker logs -f docker-dashboard-1"
    echo "  Restart dashboard:  docker compose -f $REPO_DIR/docker/docker-compose.yml restart"
    echo "  Check services:     systemctl status docker-dashboard.service"
    echo "                      systemctl status kiosk-chromium.service"
    echo ""
    echo "${BLUE}Configuration Files:${NC}"
    echo "  Environment:        $REPO_DIR/.env"
    echo "  Playlists:          $REPO_DIR/playlists.json"
    echo "  Setup Guide:        $REPO_DIR/docs/RASPBERRY_PI_SETUP.md"
    echo ""
    echo "${GREEN}Happy dashboarding! 🎉${NC}"
    echo ""
}

# ============================================
# Main Execution
# ============================================

main() {
    welcome_message
    update_system
    install_docker
    install_packages
    setup_repository
    configure_environment
    start_docker_container
    setup_systemd_services
    configure_autologin
    disable_screen_blanking
    print_next_steps
}

# Run main function
main
