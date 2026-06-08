# Telegram Dating Bot

Myanmar-only Telegram dating bot MVP using Python, Kurigram, and MongoDB.

## Features

- Anonymous limited browsing.
- Complete profiles with photo, bio, age, gender, interested-in gender, and Telegram shared location.
- Myanmar-only location validation with reverse geocoding and MongoDB cache.
- Like/pass browsing, mutual matches, and contact reveal only after both users match.
- Report, block, and admin ban/unban flows.
- English and Burmese message catalogs.
- Native Ubuntu deployment with `systemd`; no Docker.

## Local Setup

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
```

Edit `.env` with your Telegram API credentials, bot token, MongoDB URI, and admin user IDs.

Run the bot:

```bash
python -m bot.main
```

Run tests:

```bash
pytest
```

## Native Ubuntu Deployment

See [deploy/ubuntu.md](deploy/ubuntu.md) and [deploy/telegram-dating-bot.service](deploy/telegram-dating-bot.service).

The app expects MongoDB to be reachable from `MONGODB_URI`. You can use a local MongoDB package on the VPS or a remote managed MongoDB instance.

