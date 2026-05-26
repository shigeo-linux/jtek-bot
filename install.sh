#!/bin/bash
set -e

SYSTEMD_USER_DIR="$HOME/.config/systemd/user"
CONFIG_DIR="$HOME/.config/jtek-bot"
BOT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=== Installing JTEK/VOO/SGOV Rotation Bot ==="

echo "Installing Python dependencies..."
pip3 install --quiet --user yfinance hmmlearn pandas numpy requests

echo "Creating config directory..."
mkdir -p "$CONFIG_DIR"

# Prompt for Telegram credentials if not already configured
CONFIG_FILE="$CONFIG_DIR/config.json"
if [ ! -f "$CONFIG_FILE" ]; then
    echo ""
    read -rp "Telegram bot token: " TG_TOKEN
    read -rp "Telegram chat ID:   " TG_CHAT
    cat > "$CONFIG_FILE" << EOF
{
  "telegram_token": "${TG_TOKEN}",
  "telegram_chat_id": "${TG_CHAT}",
  "lookback_days": 756,
  "n_states": 3,
  "n_restarts": 20
}
EOF
    echo "Config written to $CONFIG_FILE"
else
    echo "Config already exists at $CONFIG_FILE — skipping credential prompt."
fi

echo "Installing systemd user timer..."
mkdir -p "$SYSTEMD_USER_DIR"
cp "$BOT_DIR/jtek-bot.service" "$SYSTEMD_USER_DIR/jtek-bot.service"
cp "$BOT_DIR/jtek-bot.timer"   "$SYSTEMD_USER_DIR/jtek-bot.timer"

sudo loginctl enable-linger "$(whoami)"

export XDG_RUNTIME_DIR="/run/user/$(id -u)"
export DBUS_SESSION_BUS_ADDRESS="unix:path=${XDG_RUNTIME_DIR}/bus"

if systemctl --user daemon-reload 2>/dev/null; then
    systemctl --user enable jtek-bot.timer
    systemctl --user start  jtek-bot.timer
    echo "Timer enabled — runs daily at 22:00 Oslo time."
else
    echo "Note: run 'systemctl --user enable --now jtek-bot.timer' after login."
fi

echo ""
echo "=== Installation complete! ==="
echo ""
echo "Test run:     python3 $BOT_DIR/runner.py"
echo "View logs:    tail -f $CONFIG_DIR/jtek-bot.log"
echo "Timer status: systemctl --user status jtek-bot.timer"
