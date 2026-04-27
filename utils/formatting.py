"""
Unicode text styling utilities.
Converts regular text to bold mathematical alphanumeric symbols
and small-caps stylings for premium Telegram bot output.
"""

# Mapping for bold mathematical symbols (𝐀-𝐙, 𝐚-𝐳, 𝟎-𝟗)
_BOLD_UPPER = "𝐀𝐁𝐂𝐃𝐄𝐅𝐆𝐇𝐈𝐉𝐊𝐋𝐌𝐍𝐎𝐏𝐐𝐑𝐒𝐓𝐔𝐕𝐖𝐗𝐘𝐙"
_BOLD_LOWER = "𝐚𝐛𝐜𝐝𝐞𝐟𝐠𝐡𝐢𝐣𝐤𝐥𝐦𝐧𝐨𝐩𝐪𝐫𝐬𝐭𝐮𝐯𝐰𝐱𝐲𝐳"
_BOLD_DIGITS = "𝟎𝟏𝟐𝟑𝟒𝟓𝟔𝟕𝟖𝟗"

# Small caps mapping (ᴀʙᴄᴅᴇғɢʜɪᴊᴋʟᴍɴᴏᴘǫʀsᴛᴜᴠᴡxʏᴢ)
_SMALL_UPPER = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
_SMALL_LOWER = "abcdefghijklmnopqrstuvwxyz"
_SMALL_DIGITS = "0123456789"

_BOLD_TRANS = str.maketrans(
    _SMALL_UPPER + _SMALL_LOWER + _SMALL_DIGITS,
    _BOLD_UPPER + _BOLD_LOWER + _BOLD_DIGITS,
)

# Small caps mapping (approximate using Unicode small caps)
_SMALL_CAPS_MAP = {
    "a": "ᴀ", "b": "ʙ", "c": "ᴄ", "d": "ᴅ", "e": "ᴇ", "f": "ғ",
    "g": "ɢ", "h": "ʜ", "i": "ɪ", "j": "ᴊ", "k": "ᴋ", "l": "ʟ",
    "m": "ᴍ", "n": "ɴ", "o": "ᴏ", "p": "ᴘ", "q": "ǫ", "r": "ʀ",
    "s": "s", "t": "ᴛ", "u": "ᴜ", "v": "ᴠ", "w": "ᴡ", "x": "x",
    "y": "ʏ", "z": "ᴢ",
    "A": "ᴀ", "B": "ʙ", "C": "ᴄ", "D": "ᴅ", "E": "ᴇ", "F": "ғ",
    "G": "ɢ", "H": "ʜ", "I": "ɪ", "J": "ᴊ", "K": "ᴋ", "L": "ʟ",
    "M": "ᴍ", "N": "ɴ", "O": "ᴏ", "P": "ᴘ", "Q": "ǫ", "R": "ʀ",
    "S": "s", "T": "ᴛ", "U": "ᴜ", "V": "ᴠ", "W": "ᴡ", "X": "x",
    "Y": "ʏ", "Z": "ᴢ",
}


def bold(text: str) -> str:
    """Convert regular Latin letters and digits to bold Unicode mathematical symbols."""
    return text.translate(_BOLD_TRANS)


def small_caps(text: str) -> str:
    """Convert text to small-caps style (approximate Unicode small caps)."""
    return "".join(_SMALL_CAPS_MAP.get(ch, ch) for ch in text)


def styled_block(lines: list, border_char: str = "━") -> str:
    """Wrap lines inside a decorative border block quote style."""
    if not lines:
        return ""
    max_len = max(len(line) for line in lines)
    border = border_char * (max_len + 4)
    result = [border]
    for line in lines:
        result.append(f"{border_char} {line.ljust(max_len)} {border_char}")
    result.append(border)
    return "\n".join(result)


def now_playing_text(title: str, artist: str, duration: str, requested_by: str, volume: int) -> str:
    """Returns the stylised 'Now Playing' caption."""
    lines = [
        bold("🎧 NOW PLAYING"),
        "",
        f"╰⟡ {bold('Title')}     : {bold(title)}",
        f"╰⟡ {bold('Artist')}    : {bold(artist)}",
        f"╰⟡ {bold('Duration')}  : {bold(duration)}",
        f"╰⟡ {bold('Requested')} : {bold(requested_by)}",
        f"╰⟡ {bold('Volume')}    : {bold(f'{volume}%')}",
        "",
        bold("▰▰▰▰▰▰▱▱▱"),
        bold("⚡ PLAYING"),
    ]
    return "\n".join(lines)


def queue_text(tracks: list) -> str:
    """
    tracks -> list of dicts: {index, title, artist, duration}
    Returns stylised queue list.
    """
    if not tracks:
        return bold("📜 Queue is empty.")
    lines = [bold("📜 QUEUE LIST"), ""]
    for t in tracks:
        idx = t.get("index", "")
        title = t.get("title", "Unknown")
        artist = t.get("artist", "Unknown")
        duration = t.get("duration", "?")
        line = f"{idx} {bold(title)} — {bold(artist)}        ({bold(duration)})"
        lines.append(line)
    lines.append("")
    lines.append(bold(f"💿 Total: {len(tracks)} Tracks"))
    return "\n".join(lines)


def search_results_text(results: list) -> str:
    """
    results -> list of dicts: {index, title, artist}
    """
    if not results:
        return bold("🔎 No results found.")
    lines = [bold("🔎 SEARCH RESULTS"), ""]
    for r in results:
        idx = r.get("index", "")
        title = r.get("title", "Unknown")
        artist = r.get("artist", "Unknown")
        lines.append(f"{idx} {bold(title)} — {bold(artist)}")
    lines.append("")
    lines.append(bold("📩 Reply with number to play"))
    return "\n".join(lines)


def controls_text() -> str:
    """Player controls help text."""
    lines = [
        bold("⚙️ PLAYER CONTROLS"),
        "",
        bold("╰⟡ /play <name/url>   → Play"),
        bold("╰⟡ /pause            → Pause"),
        bold("╰⟡ /resume           → Resume"),
        bold("╰⟡ /skip             → Skip"),
        bold("╰⟡ /stop             → Stop"),
        bold("╰⟡ /queue            → Queue"),
        bold("╰⟡ /volume <1-100>  → Volume"),
    ]
    return "\n".join(lines)


def activate_text() -> str:
    return small_caps("✨ Activating your request.... please hold on.")


def error_text(msg: str) -> str:
    return bold(f"❌ {msg}")


def success_text(msg: str) -> str:
    return bold(f"✅ {msg}")


def info_text(msg: str) -> str:
    return bold(f"ℹ️ {msg}")
