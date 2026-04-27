"""
Flask Admin Dashboard with authentication, CSRF, rate-limiting, and REST API.
"""

import os
import secrets
from functools import wraps

import bcrypt
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, abort
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

import config
from database.db import (
    init_db,
    get_admin,
    add_admin,
    get_assistant_config,
    set_assistant_config,
    get_queue,
    clear_queue,
    remove_queue_item,
    get_all_active_chats,
    get_settings,
    set_loop,
    set_volume,
)

app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = config.SECRET_KEY

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://",
)

# ── Auth helpers ──────────────────────────────────────

def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


def generate_csrf():
    if "csrf" not in session:
        session["csrf"] = secrets.token_urlsafe(32)
    return session["csrf"]


def validate_csrf():
    token = request.headers.get("X-CSRF-Token", "") or request.form.get("csrf_token", "")
    if not token or token != session.get("csrf"):
        abort(403, "Invalid CSRF token")

# ── Pages ─────────────────────────────────────────────

@app.route("/login", methods=["GET", "POST"])
@limiter.limit("5 per minute")
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = await_sync(get_admin(username))
        if user and bcrypt.checkpw(password.encode(), user["password_hash"]):
            session["logged_in"] = True
            session["username"] = username
            generate_csrf()
            return redirect(url_for("index"))
        return render_template("login.html", error="Invalid credentials")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/")
@login_required
def index():
    return render_template("dashboard.html", csrf=generate_csrf(), developer=config.DEVELOPER)

# ── API ───────────────────────────────────────────────

@app.route("/api/status")
@login_required
def api_status():
    from main import assistant_mgr, bot_client
    active = await_sync(get_all_active_chats())
    return jsonify({
        "assistant_connected": assistant_mgr.is_connected if assistant_mgr else False,
        "bot_running": bot_client.is_connected if bot_client else False,
        "active_chats": [dict(r) for r in active],
    })


@app.route("/api/queue/<int:chat_id>")
@login_required
def api_queue(chat_id):
    rows = await_sync(get_queue(chat_id))
    return jsonify({"queue": [dict(r) for r in rows]})


@app.route("/api/assistant/config", methods=["GET", "POST"])
@login_required
def api_assistant_config():
    if request.method == "POST":
        validate_csrf()
        data = request.get_json(force=True, silent=True) or request.form
        api_id = (data.get("api_id") or "").strip()
        api_hash = (data.get("api_hash") or "").strip()
        session_str = (data.get("session_string") or "").strip()
        await_sync(set_assistant_config(api_id, api_hash, session_str))
        return jsonify({"success": True})
    cfg = await_sync(get_assistant_config())
    return jsonify({"api_id": cfg["api_id"], "api_hash": cfg["api_hash"], "session_string": "***"})


@app.route("/api/assistant/connect", methods=["POST"])
@login_required
def api_assistant_connect():
    validate_csrf()
    from main import assistant_mgr
    try:
        run_async(assistant_mgr.connect())
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/assistant/disconnect", methods=["POST"])
@login_required
def api_assistant_disconnect():
    validate_csrf()
    from main import assistant_mgr
    try:
        run_async(assistant_mgr.disconnect())
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/assistant/restart", methods=["POST"])
@login_required
def api_assistant_restart():
    validate_csrf()
    from main import assistant_mgr
    try:
        run_async(assistant_mgr.restart())
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/play", methods=["POST"])
@login_required
def api_play():
    validate_csrf()
    data = request.get_json(force=True, silent=True) or {}
    chat_id = int(data.get("chat_id", 0))
    title = data.get("title", "Dashboard Request")
    file_path = data.get("file_path", "")
    requested_by = data.get("requested_by", "admin")
    if not chat_id:
        return jsonify({"success": False, "error": "chat_id required"}), 400
    from main import assistant_mgr
    meta = {"title": title, "artist": "", "duration": "", "file_path": file_path, "requested_by": requested_by}
    try:
        run_async(assistant_mgr.play(chat_id, file_path, meta))
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/skip", methods=["POST"])
@login_required
def api_skip():
    validate_csrf()
    data = request.get_json(force=True, silent=True) or {}
    chat_id = int(data.get("chat_id", 0))
    from main import assistant_mgr
    run_async(assistant_mgr.skip(chat_id))
    return jsonify({"success": True})


@app.route("/api/stop", methods=["POST"])
@login_required
def api_stop():
    validate_csrf()
    data = request.get_json(force=True, silent=True) or {}
    chat_id = int(data.get("chat_id", 0))
    from main import assistant_mgr
    run_async(assistant_mgr.stop(chat_id))
    return jsonify({"success": True})


@app.route("/api/pause", methods=["POST"])
@login_required
def api_pause():
    validate_csrf()
    data = request.get_json(force=True, silent=True) or {}
    chat_id = int(data.get("chat_id", 0))
    from main import assistant_mgr
    run_async(assistant_mgr.pause(chat_id))
    return jsonify({"success": True})


@app.route("/api/resume", methods=["POST"])
@login_required
def api_resume():
    validate_csrf()
    data = request.get_json(force=True, silent=True) or {}
    chat_id = int(data.get("chat_id", 0))
    from main import assistant_mgr
    run_async(assistant_mgr.resume(chat_id))
    return jsonify({"success": True})


@app.route("/api/queue/clear", methods=["POST"])
@login_required
def api_queue_clear():
    validate_csrf()
    data = request.get_json(force=True, silent=True) or {}
    chat_id = int(data.get("chat_id", 0))
    await_sync(clear_queue(chat_id))
    return jsonify({"success": True})


@app.route("/api/queue/remove", methods=["POST"])
@login_required
def api_queue_remove():
    validate_csrf()
    data = request.get_json(force=True, silent=True) or {}
    chat_id = int(data.get("chat_id", 0))
    index = int(data.get("index", 0))
    ok = await_sync(remove_queue_item(chat_id, index))
    return jsonify({"success": ok})


@app.route("/api/settings", methods=["GET", "POST"])
@login_required
def api_settings():
    if request.method == "POST":
        validate_csrf()
        data = request.get_json(force=True, silent=True) or {}
        chat_id = int(data.get("chat_id", 0))
        loop = 1 if data.get("loop") else 0
        vol = int(data.get("volume", 100))
        await_sync(set_loop(chat_id, loop))
        await_sync(set_volume(chat_id, vol))
        return jsonify({"success": True})
    chat_id = int(request.args.get("chat_id", 0))
    s = await_sync(get_settings(chat_id))
    return jsonify(s)

# ── Async bridge for assistant (runs in main loop) ────

_main_loop = None


def set_main_loop(loop):
    global _main_loop
    _main_loop = loop


def run_async(coro):
    if _main_loop is None:
        raise RuntimeError("Main loop not running")
    import asyncio
    return asyncio.run_coroutine_threadsafe(coro, _main_loop).result()


# ── Sync wrapper for async DB functions ───────────────

def await_sync(coro):
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)
    import concurrent.futures
    with concurrent.futures.ThreadPoolExecutor() as pool:
        def run():
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            return new_loop.run_until_complete(coro)
        return pool.submit(run).result()

# ── Admin seed ──────────────────────────────────────────

async def seed_admin():
    pw = config.ADMIN_PASSWORD.encode()
    h = bcrypt.hashpw(pw, bcrypt.gensalt())
    await init_db()
    await add_admin(config.ADMIN_USERNAME, h)

