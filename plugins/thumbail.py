import os
import asyncio
from presets import Presets
from pyrogram import Client, filters
from pyrogram.types import Message

if bool(os.environ.get("ENV", False)):
    from sample_config import Config
else:
    from config import Config


@Client.on_message(filters.private & filters.photo)
async def save_photo(bot: Client, m: Message):
    msg = await m.reply_text(Presets.WAIT_MESSAGE, reply_to_message_id=m.message_id)

    # Auth check
    if Config.AUTH_USERS and (m.from_user.id not in Config.AUTH_USERS):
        await m.delete()
        await msg.edit_text(Presets.NOT_AUTH_TXT)
        await asyncio.sleep(5)
        await msg.delete()
        return

    # Ensure thumbnails folder exists
    thumbs_dir = os.path.join(os.getcwd(), "thumbnails")
    os.makedirs(thumbs_dir, exist_ok=True)

    thumb_image = os.path.join(thumbs_dir, f"{m.from_user.id}.jpg")

    # Download media
    try:
        await bot.download_media(m, thumb_image)
        await msg.edit_text(Presets.SAVED_THUMB)
    except Exception as e:
        await msg.edit_text(f"⚠️ Failed to save photo: {e}")

    # Optional: delete confirmation message after 5 seconds
    await asyncio.sleep(5)
    await msg.delete()
