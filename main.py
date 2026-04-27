"""
Entry point — starts:
  1. SQLite DB + admin seed
  2. Assistant (Pyrogram user + pytgcalls)
  3. Telegram Bot (Pyrogram bot)
  4. Flask Dashboard (in background thread)
Run: python main.py
"""

import asyncio
import sys

# === FIX: Create event loop for Python 3.14 compatibility ===
# This must run BEFORE any pyrogram imports
if sys.version_info >= (3, 14):
    try:
        asyncio.get_event_loop()
    except RuntimeError:
        asyncio.set_event_loop(asyncio.new_event_loop())
# ============================================================

import threading
import logging

from database.db import init_db, add_admin, get_admin
from dashboard.app import app, seed_admin
from core.assistant import AssistantManager
from bot.bot_client import build_bot
import config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
)

assistant_mgr: AssistantManager = None
bot_client = None
main_loop: asyncio.AbstractEventLoop = None


def run_async(coro):
    """Thread-safe helper to run a coroutine in the main event loop."""
    if main_loop is None:
        raise RuntimeError("Main loop not running")
    return asyncio.run_coroutine_threadsafe(coro, main_loop).result()


async def main():
    global assistant_mgr, bot_client, main_loop
    main_loop = asyncio.get_running_loop()

    # ── Init database ───────────────────────────────────
    await init_db()
    # Seed default admin if missing
    existing = await get_admin(config.ADMIN_USERNAME)
    if not existing:
        await seed_admin()
        print(f"[INIT] Default admin created: {config.ADMIN_USERNAME}")

    # ── Create assistant & bot ──────────────────────────
    assistant_mgr = AssistantManager()
    bot_client = build_bot(assistant_mgr)

    # Optionally auto-connect assistant if credentials are in env
    if config.API_ID and config.API_HASH and (config.SESSION_STRING or True):
        try:
            await assistant_mgr.connect()
            print("[ASSISTANT] Connected automatically from env config.")
        except Exception as e:
            print(f"[ASSISTANT] Auto-connect failed (configure via dashboard): {e}")

    # Start bot
    await bot_client.start()
    print("[BOT] Started.")

    # ── Start Flask in background thread ────────────────
    from dashboard.app import set_main_loop
    set_main_loop(main_loop)

    def run_flask():
        app.run(
            host=config.DASHBOARD_HOST,
            port=config.DASHBOARD_PORT,
            debug=False,
            use_reloader=False,
            threaded=True,
        )

    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    print(f"[DASHBOARD] Running on http://{config.DASHBOARD_HOST}:{config.DASHBOARD_PORT}")

    # ── Keep alive ──────────────────────────────────────
    print("[SYSTEM] All services running. Press Ctrl+C to stop.")
    stop_event = asyncio.Event()
    try:
        await stop_event.wait()
    except (KeyboardInterrupt, asyncio.CancelledError):
        pass
    finally:
        print("[SYSTEM] Shutting down...")
        await bot_client.stop()
        await assistant_mgr.disconnect()
        print("[SYSTEM] Goodbye.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
