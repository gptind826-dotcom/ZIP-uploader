# Telegram Music Bot with Admin Dashboard

A secure, full-stack Telegram Music Bot powered by **Python**, **Flask**, **Pyrogram**, **py-tgcalls**, and **SQLite**.

**Developed by @EXUCODR**

---

## Features

- **Telegram Bot** handles music commands with bold Unicode styling.
- **Assistant Account** (userbot) streams audio in Telegram voice chats.
- **Auto-Join**: Automatically detects when a live stream / voice chat starts and joins instantly.
- **Admin Web Dashboard** for full system control (assistant config, playback controls, queue, settings).
- **Secure Authentication**: bcrypt hashed passwords, Flask sessions, CSRF tokens, rate-limited login.
- **Queue System** with loop mode and volume control.
- **YouTube Search & Download** via yt-dlp.

---

## Tech Stack

| Layer | Tech |
|-------|------|
| Backend | Python 3.9+, Flask, aiosqlite |
| Bot | Pyrogram (bot + assistant user) |
| Voice | py-tgcalls 2.0.6 (MediaStream) |
| DB | SQLite |
| Dashboard | Bootstrap 5 + Vanilla JS |

---

## Project Structure

```
music_bot/
├── main.py                  # Entry point
├── config.py                # Environment config
├── requirements.txt         # Dependencies
├── .env.example             # Example environment file
├── database/
│   └── db.py                # Async SQLite layer
├── core/
│   ├── assistant.py         # Assistant + py-tgcalls manager
│   └── downloader.py        # YouTube downloader + search
├── bot/
│   └── bot_client.py        # Telegram bot commands
├── dashboard/
│   ├── app.py               # Flask app + API
│   ├── templates/
│   │   ├── login.html
│   │   └── dashboard.html
│   └── static/              # (optional assets)
├── utils/
│   └── formatting.py        # Bold Unicode + small-caps styling
└── downloads/               # Audio cache
```

---

## Setup Guide

### 1. Clone / Download

```bash
cd ~/music_bot
```

### 2. Install Python 3.9+

**Termux:**
```bash
pkg update
pkg install python ffmpeg git -y
```

**Linux / macOS:**
```bash
sudo apt update
sudo apt install python3 python3-pip ffmpeg -y
```

### 3. Install Python Dependencies

```bash
pip install -r requirements.txt
```

> Note: `py-tgcalls` ships with prebuilt wheels. If installation fails on an unsupported architecture, ensure `ffmpeg` is installed and try:
> ```bash
> pip install py-tgcalls --no-deps
> pip install aiohttp ntgcalls psutil screeninfo deprecation
> ```

### 4. Configure Environment

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
nano .env
```

| Variable | Description |
|----------|-------------|
| `API_ID` | Telegram API ID (from my.telegram.org) |
| `API_HASH` | Telegram API HASH |
| `BOT_TOKEN` | Bot token from @BotFather |
| `SECRET_KEY` | Random string for Flask sessions |
| `ADMIN_USERNAME` | Default dashboard username |
| `ADMIN_PASSWORD` | Default dashboard password |
| `SESSION_STRING` | (Optional) Assistant session string |

**Get Assistant Session String (optional):**

If you leave `SESSION_STRING` empty, you can generate one later via the Dashboard after entering `API_ID` and `API_HASH`, or use a small script:

```python
from pyrogram import Client
app = Client("assistant", api_id=YOUR_API_ID, api_hash="YOUR_API_HASH")
with app:
    print(app.export_session_string())
```

### 5. Run the Bot

```bash
python main.py
```

On first run, the database is initialized and the default admin account is created.

---

## Default Admin Credentials

| Field | Value |
|-------|-------|
| Username | `admin` (or your `ADMIN_USERNAME`) |
| Password | `admin123` (or your `ADMIN_PASSWORD`) |

Login at: `http://localhost:5000/login`

---

## Bot Commands

| Command | Description |
|---------|-------------|
| `/play <name/url>` | Play a song or add to queue |
| `/search <name>` | Search YouTube and pick by number |
| `/skip` | Skip current track |
| `/stop` | Stop and leave voice chat |
| `/pause` | Pause playback |
| `/resume` | Resume playback |
| `/queue` | Show current queue |
| `/volume <1-100>` | Set volume |
| `/start` | Show welcome + controls |

---

## Dashboard API Endpoints

All endpoints require authentication (`Cookie: session=...`) and a `X-CSRF-Token` header.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/status` | System status + active chats |
| GET | `/api/queue/<chat_id>` | Queue for a chat |
| GET/POST | `/api/assistant/config` | Get / save assistant credentials |
| POST | `/api/assistant/connect` | Connect assistant |
| POST | `/api/assistant/disconnect` | Disconnect assistant |
| POST | `/api/assistant/restart` | Restart assistant |
| POST | `/api/play` | Play file in chat |
| POST | `/api/skip` | Skip track |
| POST | `/api/stop` | Stop playback |
| POST | `/api/pause` | Pause playback |
| POST | `/api/resume` | Resume playback |
| POST | `/api/queue/clear` | Clear queue |
| POST | `/api/queue/remove` | Remove track by index |
| GET/POST | `/api/settings` | Get / update chat settings |

---

## Output Styling

All bot replies use **bold mathematical Unicode** characters and **small-caps** activation messages for a premium look:

- **Now Playing** captions with decorative borders
- **Queue** lists with numbered bullets
- **Search results** with reply-to-play instructions
- **Controls** help in bold block style

---

## Security Notes

- Passwords are hashed with **bcrypt**.
- Dashboard routes are protected by **Flask sessions**.
- Forms/API require **CSRF tokens**.
- Login is **rate-limited** (5 attempts per minute).
- Assistant credentials are stored in **SQLite** (or can be encrypted via environment variables).

---

## Troubleshooting

**Bot not responding?**
- Ensure `BOT_TOKEN`, `API_ID`, `API_HASH` are correct.
- Check that `py-tgcalls` installed successfully (`pip show py-tgcalls`).

**Assistant fails to connect?**
- Verify `API_ID`, `API_HASH`, and `SESSION_STRING`.
- Make sure the assistant account is a member of the target group/channel.

**No audio in voice chat?**
- Confirm `ffmpeg` is installed: `ffmpeg -version`
- Check that downloaded audio files exist in `downloads/`.

**Port already in use?**
- Change `DASHBOARD_PORT` in `.env`.

---

## License

MIT — free to use and modify. **Developed by @EXUCODR**
