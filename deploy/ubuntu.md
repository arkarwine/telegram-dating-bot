# Native Ubuntu Deployment

These steps run the bot directly on Ubuntu with Python, MongoDB, and `systemd`.

## 1. Install packages

```bash
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3-pip git
```

Install MongoDB from MongoDB's official Ubuntu repository, or use MongoDB Atlas and set `MONGODB_URI` to the Atlas URI. Ubuntu's default repositories often do not include the current `mongodb-org` package.

## 2. Create app user and directory

```bash
sudo useradd --system --create-home --shell /usr/sbin/nologin telegrambot
sudo mkdir -p /opt/telegram-dating-bot
sudo chown telegrambot:telegrambot /opt/telegram-dating-bot
```

Copy or clone this repository into `/opt/telegram-dating-bot`.

## 3. Install Python dependencies

```bash
cd /opt/telegram-dating-bot
sudo -u telegrambot python3.11 -m venv .venv
sudo -u telegrambot .venv/bin/pip install -e .
sudo -u telegrambot cp .env.example .env
```

Edit `/opt/telegram-dating-bot/.env`.

## 4. Install the service

```bash
sudo cp deploy/telegram-dating-bot.service /etc/systemd/system/telegram-dating-bot.service
sudo systemctl daemon-reload
sudo systemctl enable telegram-dating-bot
sudo systemctl start telegram-dating-bot
sudo journalctl -u telegram-dating-bot -f
```
