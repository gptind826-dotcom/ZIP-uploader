# patch_pyrogram.py
import asyncio
import sys

def patch_asyncio_for_pyrogram():
    """Fix for pyrogram compatibility with Python 3.14+"""
    if sys.version_info >= (3, 14):
        try:
            asyncio.get_event_loop()
        except RuntimeError:
            asyncio.set_event_loop(asyncio.new_event_loop())

# Execute the patch immediately when this module is imported
patch_asyncio_for_pyrogram()
