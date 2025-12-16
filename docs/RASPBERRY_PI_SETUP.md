# Raspberry Pi 5 Setup Guide

Complete guide for deploying the Home Dashboard on a Raspberry Pi 5 with touchscreen display.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Setup (Automated)](#quick-setup-automated)
- [Manual Setup](#manual-setup)
- [Post-Installation](#post-installation)
- [Troubleshooting](#troubleshooting)
- [Maintenance](#maintenance)

---

## Prerequisites

### Hardware

- Raspberry Pi 5 (4GB+ RAM recommended)
- MicroSD card (32GB+ recommended)
- Touchscreen display
- Power supply for Pi 5
- Keyboard and mouse (for initial setup)

### Software & Services

You'll need accounts and API keys for:

1. **OpenWeather API**
   - Sign up at [openweathermap.org](https://openweathermap.org/api)
   - Get your free API key

2. **Spotify Developer**
   - Create app at [developer.spotify.com](https://developer.spotify.com/dashboard)
   - Note your Client ID and Client Secret
   - Set redirect URI: `http://localhost:8000/api/spotify/auth/callback`

3. **IFTTT** (optional, for phone notifications)
   - Create applet at [ifttt.com](https://ifttt.com)
   - Get webhook key from Webhooks service

4. **Samsung TV** (if applicable)
   - Note your TV's IP address on your network

### Initial SD Card Setup

1. Download [Raspberry Pi Imager](https://www.raspberrypi.com/software/)
2. Flash **Raspberry Pi OS (64-bit)** to microSD card
3. Click settings gear icon (⚙️) and configure:
   - ✅ Enable SSH
   - ✅ Set hostname (e.g., `dashboard`)
   - ✅ Set username and password
   - ✅ Configure WiFi (SSID and password)
   - ✅ Set timezone
4. Write to SD card
5. Insert SD card into Pi 5 and boot

---

## Quick Setup (Automated)

The automated script handles most of the installation process.

### Step 1: Connect to Your Pi

```bash
# From your computer, SSH into the Pi
ssh your-username@dashboard.local
```

### Step 2: Run the Setup Script

```bash
# Download and run the setup script
curl -fsSL https://raw.githubusercontent.com/jphproductions/home-dashboard/main/scripts/pi-setup.sh -o pi-setup.sh
chmod +x pi-setup.sh
./pi-setup.sh
```

The script will:

- Update system packages
- Install Docker and Docker Compose
- Install required packages (Chromium, unclutter, xdotool)
- Clone the repository
- Guide you through `.env` configuration
- Set up systemd services
- Configure kiosk mode
- Disable screen blanking

### Step 3: Configure Environment Variables

The script will prompt you for:

- Dashboard API key (generate a secure random string)
- TV IP address
- Weather API key and location coordinates
- Spotify Client ID, Client Secret
- IFTTT webhook key (optional)

### Step 4: Get Spotify Refresh Token

After the script completes:

1. Open browser to: `http://dashboard.local:8000/api/spotify/auth/login`
2. Authorize with Spotify
3. Copy the refresh token displayed
4. Update `.env`:

   ```bash
   cd ~/home-dashboard
   nano .env
   # Add: SPOTIFY_REFRESH_TOKEN=your_token_here
   ```

5. Restart the dashboard:

   ```bash
   docker compose -f docker/docker-compose.yml restart
   ```

### Step 5: Reboot

```bash
sudo reboot
```

After reboot, your dashboard should automatically display in kiosk mode! 🎉

---

## Manual Setup

For those who prefer to understand each step or customize the installation.

### Step 1: Connect to Your Pi

```bash
ssh your-username@dashboard.local
```

### Step 2: Update System

```bash
sudo apt update && sudo apt upgrade -y
```

### Step 3: Install Docker

```bash
# Download and run Docker installation script
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add your user to docker group
sudo usermod -aG docker $USER

# Apply group membership (or logout/login)
newgrp docker

# Verify installation
docker --version
docker compose version
```

### Step 4: Install Required Packages

```bash
# Install Chromium for kiosk mode and utilities
sudo apt install -y chromium-browser unclutter xdotool git

# Verify installation
chromium-browser --version
```

### Step 5: Clone Repository

```bash
cd ~
git clone https://github.com/jphproductions/home-dashboard.git
cd home-dashboard
```

### Step 6: Configure Environment

```bash
# Create .env file
nano .env
```

Populate with your configuration:

```env
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_BASE_URL=http://localhost:8000
DASHBOARD_API_KEY=your-secure-random-key-here

# TV Configuration
TV_IP=192.168.1.100
TV_SPOTIFY_DEVICE_ID=your-tv-spotify-device-id

# Weather Configuration
WEATHER_API_KEY=your-openweather-api-key
WEATHER_LOCATION=Amsterdam
WEATHER_LATITUDE=52.3676
WEATHER_LONGITUDE=4.9041

# Spotify Configuration
SPOTIFY_CLIENT_ID=your-spotify-client-id
SPOTIFY_CLIENT_SECRET=your-spotify-client-secret
SPOTIFY_REDIRECT_URI=http://localhost:8000/api/spotify/auth/callback
SPOTIFY_REFRESH_TOKEN=  # Leave empty for now

# IFTTT Configuration (optional)
IFTTT_WEBHOOK_KEY=your-ifttt-webhook-key
IFTTT_EVENT_NAME=ring_phone

# CORS and Security
CORS_ORIGINS=http://localhost:8000,http://dashboard.local:8000
TRUSTED_HOSTS=localhost,dashboard.local,127.0.0.1

# Logging
LOG_LEVEL=INFO
```

Save and exit (`Ctrl+X`, `Y`, `Enter`)

### Step 7: Start Docker Container

```bash
# Build and start the container
docker compose -f docker/docker-compose.yml up -d

# Verify it's running
docker ps

# Check logs
docker logs -f home-dashboard-dashboard-1

# Test the endpoint
curl http://localhost:8000/health
```

### Step 8: Get Spotify Refresh Token

1. **From the Pi's desktop** (or another device on your network):

   ```bash
   chromium-browser http://localhost:8000/api/spotify/auth/login
   ```

2. **Authorize the application** with your Spotify account

3. **Copy the refresh token** displayed on the callback page

4. **Update `.env`**:

   ```bash
   nano .env
   # Update: SPOTIFY_REFRESH_TOKEN=the_token_you_copied
   ```

5. **Restart the container**:

   ```bash
   docker compose -f docker/docker-compose.yml restart
   ```

### Step 9: Install Systemd Services

#### Docker Dashboard Service (Auto-start on boot)

```bash
# Copy service file
sudo cp infra/systemd/docker-dashboard.service /etc/systemd/system/

# Edit if needed (check paths and user)
sudo nano /etc/systemd/system/docker-dashboard.service

# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable docker-dashboard.service
sudo systemctl start docker-dashboard.service

# Check status
sudo systemctl status docker-dashboard.service
```

#### Chromium Kiosk Service

```bash
# Copy service file
sudo cp infra/systemd/kiosk-chromium.service /etc/systemd/system/

# Edit to match your username
sudo nano /etc/systemd/system/kiosk-chromium.service
# Ensure User= matches your Pi username

# Enable (will start after graphical.target)
sudo systemctl daemon-reload
sudo systemctl enable kiosk-chromium.service

# Don't start yet - needs desktop environment
```

### Step 10: Configure Auto-login

For kiosk mode to work, the Pi needs to auto-login to the desktop:

```bash
sudo raspi-config
```

Navigate to:

- **System Options** → **Boot / Auto Login** → **Desktop Autologin**
- Select and confirm

### Step 11: Disable Screen Blanking

#### Configure LightDM

```bash
sudo nano /etc/lightdm/lightdm.conf
```

Add under `[Seat:*]`:

```ini
[Seat:*]
xserver-command=X -s 0 -dpms
```

#### Configure LXDE Autostart

```bash
mkdir -p ~/.config/lxsession/LXDE-pi
nano ~/.config/lxsession/LXDE-pi/autostart
```

Add:

```plain
@xset s off
@xset -dpms
@xset s noblank
```

### Step 12: Optional - Rotate Display

If you need to rotate your touchscreen:

```bash
sudo nano /boot/firmware/config.txt
```

Add one of:

```ini
# 90 degrees
display_rotate=1

# 180 degrees
display_rotate=2

# 270 degrees
display_rotate=3
```

### Step 13: Final Reboot

```bash
sudo reboot
```

After reboot:

- ✅ Docker container auto-starts
- ✅ Desktop auto-logs in
- ✅ Chromium launches in kiosk mode
- ✅ Dashboard displays on touchscreen

---

## Post-Installation

### Verify Everything is Running

```bash
# Check Docker container
docker ps

# Check systemd services
systemctl status docker-dashboard.service
systemctl status kiosk-chromium.service

# View dashboard logs
docker logs -f home-dashboard-dashboard-1

# Test from another device
curl http://dashboard.local:8000/health
```

### Customize Playlists

Edit `playlists.json` to add your favorite Spotify playlists:

```bash
cd ~/home-dashboard
nano playlists.json
```

Restart after editing:

```bash
docker compose -f docker/docker-compose.yml restart
```

---

## Troubleshooting

### Dashboard Not Accessible

**Check if container is running:**

```bash
docker ps
docker logs home-dashboard-dashboard-1
```

**Check if port is listening:**

```bash
sudo netstat -tlnp | grep 8000
```

**Restart container:**

```bash
docker compose -f ~/home-dashboard/docker/docker-compose.yml restart
```

### Kiosk Mode Not Starting

**Check service status:**

```bash
systemctl status kiosk-chromium.service
journalctl -u kiosk-chromium.service -f
```

**Verify auto-login is enabled:**

```bash
sudo raspi-config
# Check: System Options → Boot / Auto Login
```

**Manually test Chromium kiosk:**

```bash
DISPLAY=:0 chromium-browser --kiosk --noerrdialogs --disable-infobars --no-first-run --fast --fast-start --disable-features=TranslateUI --disk-cache-dir=/dev/null http://localhost:8000
```

### Screen Goes Blank

**Check screen blanking settings:**

```bash
# View current settings
xset q

# Disable blanking (from desktop)
xset s off
xset -dpms
xset s noblank
```

**Verify autostart file:**

```bash
cat ~/.config/lxsession/LXDE-pi/autostart
```

### Touchscreen Not Responding

**Check if touchscreen is detected:**

```bash
dmesg | grep -i touch
xinput list
```

**Calibrate touchscreen:**

```bash
sudo apt install xinput-calibrator
xinput_calibrator
```

### Spotify Not Working

**Check if refresh token is set:**

```bash
grep SPOTIFY_REFRESH_TOKEN ~/home-dashboard/.env
```

**Re-authorize:**

```bash
# Visit: http://dashboard.local:8000/api/spotify/auth/login
# Copy new token and update .env
docker compose -f ~/home-dashboard/docker/docker-compose.yml restart
```

### Container Out of Memory

**Check memory usage:**

```bash
docker stats
free -h
```

**Adjust memory limits in `docker-compose.yml`** if needed (current limit: 512MB)

---

## Maintenance

### Update Dashboard

```bash
cd ~/home-dashboard
git pull
docker compose -f docker/docker-compose.yml up -d --build
```

### View Logs

```bash
# Dashboard logs
docker logs -f home-dashboard-dashboard-1

# Systemd service logs
journalctl -u docker-dashboard.service -f
journalctl -u kiosk-chromium.service -f
```

### Restart Services

```bash
# Restart dashboard
docker compose -f ~/home-dashboard/docker/docker-compose.yml restart

# Restart systemd services
sudo systemctl restart docker-dashboard.service
sudo systemctl restart kiosk-chromium.service
```

### Backup Configuration

```bash
# Backup your .env file
cp ~/home-dashboard/.env ~/home-dashboard/.env.backup

# Backup playlists
cp ~/home-dashboard/playlists.json ~/home-dashboard/playlists.json.backup
```

### Monitor Performance

```bash
# System resources
htop

# Docker resources
docker stats

# Disk space
df -h

# Temperature
vcgencmd measure_temp
```

---

## Security Recommendations

1. **Change default password** for your Pi user
2. **Use strong API keys** - generate random strings for `DASHBOARD_API_KEY`
3. **Keep system updated**: `sudo apt update && sudo apt upgrade -y`
4. **Firewall** (optional): Configure UFW to restrict access
5. **HTTPS** (optional): Use reverse proxy (nginx) with Let's Encrypt for production

---

## Additional Resources

- [Raspberry Pi Documentation](https://www.raspberrypi.com/documentation/)
- [Docker Documentation](https://docs.docker.com/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Project Repository](https://github.com/jphproductions/home-dashboard)

---

**Need help?** Open an issue on GitHub or check the troubleshooting section above.
