"""
Assistant Manager using py-tgcalls 2.0.6 (PyTgCalls) + Pyrogram user client.
Handles playback, queue advancement, auto-join on detected group calls.
"""

import asyncio
import os
from typing import Optional

from pyrogram import Client, raw
from pytgcalls import PyTgCalls
from pytgcalls.types import MediaStream, Update
from pytgcalls.types.stream.stream_audio_ended import StreamAudioEnded

import config
from database.db import (
    get_assistant_config,
    set_active_chat,
    clear_active_chat,
    get_settings,
    pop_queue,
    add_queue,
)

SILENT_AUDIO = os.path.join(config.DOWNLOADS_DIR, "silent.mp3")


def _ensure_silent():
    if os.path.exists(SILENT_AUDIO):
        return
    import subprocess
    subprocess.run(
        [
            "ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo",
            "-t", "1", "-acodec", "libmp3lame", "-q:a", "9", SILENT_AUDIO,
        ],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True,
    )


class AssistantManager:
    def __init__(self):
        self.client: Optional[Client] = None
        self.call: Optional[PyTgCalls] = None
        # chat_id -> current track meta
        self.current: dict = {}
        # chat_id -> True if waiting for user track after silent auto-join
        self._auto_joined: dict = {}
        self._lock = asyncio.Lock()

    # ── Lifecycle ─────────────────────────────────────────

    async def connect(self):
        cfg = await get_assistant_config()
        api_id = cfg["api_id"] or str(config.API_ID)
        api_hash = cfg["api_hash"] or config.API_HASH
        session = cfg["session_string"] or config.SESSION_STRING or "assistant"

        if not api_id or not api_hash:
            raise ValueError("API_ID/API_HASH not configured")

        self.client = Client(
            name="assistant",
            api_id=int(api_id),
            api_hash=api_hash,
            session_string=session if session.startswith("BQ") or session.startswith("Ag") else None,
            workdir=config.DOWNLOADS_DIR,
        )
        await self.client.start()
        self.call = PyTgCalls(self.client)
        self.call.start()
        # Handle stream end for queue
        self.call.on_update()(self._on_update)

        # Register raw handler for auto-join
        self.client.add_handler(
            raw.handlers.RawUpdateHandler(self._raw_update_handler)
        )
        _ensure_silent()

    async def disconnect(self):
        if self.call:
            try:
                for chat_id in list(self.current.keys()):
                    try:
                        self.call.leave_call(chat_id)
                    except Exception:
                        pass
            except Exception:
                pass
            self.call = None
        self.current.clear()
        self._auto_joined.clear()
        if self.client:
            await self.client.stop()
            self.client = None

    async def restart(self):
        await self.disconnect()
        await asyncio.sleep(1)
        await self.connect()

    @property
    def is_connected(self) -> bool:
        return self.client is not None and self.client.is_connected

    # ── Auto-join handler ───────────────────────────────────

    async def _raw_update_handler(self, client, update, users, chats):
        if isinstance(update, raw.types.UpdateGroupCall):
            call = update.call
            chat_id = getattr(update, "chat_id", None)
            if chat_id is None:
                return
            if isinstance(call, raw.types.GroupCallDiscarded):
                return
            async with self._lock:
                if chat_id in self.current:
                    return  # already playing
                await self._auto_join(chat_id)

    async def _auto_join(self, chat_id: int):
        if self.call is None:
            return
        try:
            self._auto_joined[chat_id] = True
            self.call.play(chat_id, MediaStream(SILENT_AUDIO))
        except Exception as e:
            print(f"[auto-join] failed for {chat_id}: {e}")

    # ── Playback control ────────────────────────────────────

    async def play(self, chat_id: int, file_path: str, meta: dict):
        async with self._lock:
            if self.call is None:
                raise RuntimeError("Assistant not connected")
            self.current[chat_id] = meta
            self._auto_joined[chat_id] = False
            self.call.play(chat_id, MediaStream(file_path))
            await set_active_chat(chat_id, meta.get("title", ""), file_path, meta.get("requested_by", ""))

    async def skip(self, chat_id: int):
        async with self._lock:
            await self._advance(chat_id)

    async def stop(self, chat_id: int):
        async with self._lock:
            self.current.pop(chat_id, None)
            self._auto_joined.pop(chat_id, None)
            await clear_active_chat(chat_id)
            if self.call:
                try:
                    self.call.leave_call(chat_id)
                except Exception:
                    pass

    async def pause(self, chat_id: int):
        if self.call:
            try:
                self.call.pause_stream(chat_id)
            except Exception:
                pass

    async def resume(self, chat_id: int):
        if self.call:
            try:
                self.call.resume_stream(chat_id)
            except Exception:
                pass

    async def set_volume(self, chat_id: int, volume: int):
        if self.call:
            try:
                # py-tgcalls volume 1-200
                vol = max(1, min(int(volume * 2), 200))
                self.call.change_volume_call(chat_id, vol)
            except Exception:
                pass

    def get_current(self, chat_id: int) -> Optional[dict]:
        return self.current.get(chat_id)

    # ── Queue / end-of-stream logic ─────────────────────────

    async def _on_update(self, client, update: Update):
        if isinstance(update, StreamAudioEnded):
            chat_id = update.chat_id
            async with self._lock:
                if self._auto_joined.get(chat_id):
                    # If still no real track, keep looping silence to stay joined
                    if chat_id not in self.current:
                        if self.call:
                            self.call.play(chat_id, MediaStream(SILENT_AUDIO))
                    else:
                        self._auto_joined[chat_id] = False
                    return
                await self._advance(chat_id)

    async def _advance(self, chat_id: int):
        if self.call is None:
            return
        settings = await get_settings(chat_id)
        current = self.current.get(chat_id)
        if settings.get("loop") and current:
            # Replay same
            self.call.play(chat_id, MediaStream(current["file_path"]))
            return
        nxt = await pop_queue(chat_id)
        if nxt:
            meta = {
                "title": nxt["title"],
                "artist": "",
                "duration": "",
                "file_path": nxt["file_path"],
                "requested_by": nxt["requested_by"],
            }
            self.current[chat_id] = meta
            self.call.play(chat_id, MediaStream(nxt["file_path"]))
            await set_active_chat(chat_id, nxt["title"], nxt["file_path"], nxt["requested_by"])
        else:
            self.current.pop(chat_id, None)
            await clear_active_chat(chat_id)
            try:
                self.call.leave_call(chat_id)
            except Exception:
                pass
