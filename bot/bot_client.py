"""
Telegram Bot (Pyrogram) – command handlers with bold Unicode output.
Developed by @EXUCODR
"""

import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

import config
from core.downloader import download_audio, search_youtube
from core.assistant import AssistantManager
from database.db import add_queue, get_queue, clear_queue, get_settings, set_volume as db_set_volume
from utils.formatting import (
    bold,
    activate_text,
    now_playing_text,
    queue_text,
    search_results_text,
    controls_text,
    success_text,
    error_text,
)

_search_sessions: dict = {}
_paused: dict = {}  # chat_id -> bool


def build_bot(assistant: AssistantManager):
    bot = Client(
        "music_bot",
        api_id=config.API_ID,
        api_hash=config.API_HASH,
        bot_token=config.BOT_TOKEN,
    )

    def _controls_markup():
        return InlineKeyboardMarkup([
            [
                InlineKeyboardButton("⏯", callback_data="pause_resume"),
                InlineKeyboardButton("⏭", callback_data="skip"),
                InlineKeyboardButton("❌", callback_data="stop"),
            ]
        ])

    async def _send_now_playing(chat_id, meta, client):
        cap = now_playing_text(
            title=meta.get("title", "Unknown"),
            artist=meta.get("artist", "Unknown"),
            duration=meta.get("duration", "?"),
            requested_by=meta.get("requested_by", "?"),
            volume=meta.get("volume", 100),
        )
        thumb = meta.get("thumbnail")
        if thumb:
            try:
                await client.send_photo(chat_id, photo=thumb)
            except Exception:
                pass
        await client.send_message(chat_id, cap, reply_markup=_controls_markup())

    @bot.on_message(filters.command("start"))
    async def start_cmd(_, message):
        await message.reply(
            bold(f"👋 Welcome!\n\n{controls_text()}\n\n𝐃𝐞𝐯𝐞𝐥𝐨𝐩𝐞𝐝 𝐛𝐲 {config.DEVELOPER}")
        )

    @bot.on_message(filters.command("play"))
    async def play_cmd(_, message):
        query = message.text.split(None, 1)[1] if len(message.text.split()) > 1 else ""
        if not query:
            await message.reply(error_text("Provide a song name or URL.\nUsage: /play <name/url>"))
            return
        act = await message.reply(activate_text())
        try:
            if query.strip().isdigit():
                user_id = message.from_user.id
                idx = int(query.strip()) - 1
                if user_id in _search_sessions and 0 <= idx < len(_search_sessions[user_id]):
                    chosen = _search_sessions[user_id][idx]
                    info = download_audio(f"https://www.youtube.com/watch?v={chosen['video_id']}")
                else:
                    info = download_audio(query)
            else:
                info = download_audio(query)

            meta = {
                **info,
                "requested_by": message.from_user.mention or f"@{message.from_user.username}",
                "volume": 100,
            }
            chat_id = message.chat.id

            current = assistant.get_current(chat_id)
            if current:
                await add_queue(chat_id, meta["title"], meta["file_path"], meta["requested_by"])
                await act.delete()
                await message.reply(success_text(f"Added to queue: {bold(meta['title'])}"))
            else:
                await assistant.play(chat_id, meta["file_path"], meta)
                _paused[chat_id] = False
                await act.delete()
                await _send_now_playing(chat_id, meta, bot)
        except Exception as e:
            await act.delete()
            await message.reply(error_text(f"Failed to play: {e}"))

    @bot.on_message(filters.command("search"))
    async def search_cmd(_, message):
        query = message.text.split(None, 1)[1] if len(message.text.split()) > 1 else ""
        if not query:
            await message.reply(error_text("Usage: /search <song name>"))
            return
        act = await message.reply(activate_text())
        try:
            results = search_youtube(query)
            _search_sessions[message.from_user.id] = results
            await act.delete()
            await message.reply(search_results_text(results))
        except Exception as e:
            await act.delete()
            await message.reply(error_text(f"Search failed: {e}"))

    @bot.on_message(filters.command("skip"))
    async def skip_cmd(_, message):
        chat_id = message.chat.id
        await assistant.skip(chat_id)
        await message.reply(success_text("Skipped track."))

    @bot.on_message(filters.command("stop"))
    async def stop_cmd(_, message):
        chat_id = message.chat.id
        await assistant.stop(chat_id)
        _paused.pop(chat_id, None)
        await message.reply(success_text("Stopped and left voice chat."))

    @bot.on_message(filters.command("pause"))
    async def pause_cmd(_, message):
        chat_id = message.chat.id
        await assistant.pause(chat_id)
        _paused[chat_id] = True
        await message.reply(success_text("Paused."))

    @bot.on_message(filters.command("resume"))
    async def resume_cmd(_, message):
        chat_id = message.chat.id
        await assistant.resume(chat_id)
        _paused[chat_id] = False
        await message.reply(success_text("Resumed."))

    @bot.on_message(filters.command("queue"))
    async def queue_cmd(_, message):
        rows = await get_queue(message.chat.id)
        tracks = []
        digits = ["❶", "❷", "❸", "❹", "❺", "❻", "❼", "❽", "❾", "❿"]
        for i, r in enumerate(rows):
            tracks.append({
                "index": digits[i] if i < len(digits) else f"{i+1}.",
                "title": r["title"],
                "artist": "",
                "duration": "",
            })
        await message.reply(queue_text(tracks))

    @bot.on_message(filters.command("volume"))
    async def volume_cmd(_, message):
        parts = message.text.split()
        if len(parts) != 2 or not parts[1].isdigit():
            await message.reply(error_text("Usage: /volume <1-100>"))
            return
        vol = int(parts[1])
        if not (1 <= vol <= 100):
            await message.reply(error_text("Volume must be between 1 and 100."))
            return
        chat_id = message.chat.id
        await db_set_volume(chat_id, vol)
        await assistant.set_volume(chat_id, vol)
        await message.reply(success_text(f"Volume set to {vol}%"))

    @bot.on_callback_query()
    async def callback_handler(_, callback_query):
        data = callback_query.data
        chat_id = callback_query.message.chat.id
        if data == "pause_resume":
            if _paused.get(chat_id):
                await assistant.resume(chat_id)
                _paused[chat_id] = False
                await callback_query.answer(success_text("Resumed"), show_alert=False)
            else:
                await assistant.pause(chat_id)
                _paused[chat_id] = True
                await callback_query.answer(success_text("Paused"), show_alert=False)
        elif data == "skip":
            await assistant.skip(chat_id)
            await callback_query.answer(success_text("Skipped"), show_alert=False)
        elif data == "stop":
            await assistant.stop(chat_id)
            _paused.pop(chat_id, None)
            await callback_query.answer(success_text("Stopped"), show_alert=False)

    return bot
