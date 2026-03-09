import asyncio
import os
from presets import Presets
from pyrogram import Client, filters, enums
from pyrogram.types import CallbackQuery
from library.display_progress import cancel_process
from plugins.youtube_dl_button import youtube_dl_call_back
from library.buttons import reply_markup_del_thumb, reply_markup_start, reply_markup_back

if bool(os.environ.get("ENV", False)):
    from sample_config import Config
else:
    from config import Config


async def is_auth(cb: CallbackQuery):
    """Check if the user is authorized"""
    if Config.AUTH_USERS and (cb.from_user.id not in Config.AUTH_USERS):
        await cb.answer(Presets.NOT_AUTH_TXT, show_alert=True)
        return False
    return True


@Client.on_callback_query(filters.regex(r'^view_btn$'))
async def view_thumbnail(bot: Client, cb: CallbackQuery):
    if not await is_auth(cb):
        return
    thumb_image = os.path.join(os.getcwd(), "thumbnails", f"{cb.from_user.id}.jpg")
    if os.path.exists(thumb_image):
        try:
            await cb.message.delete()
        except Exception:
            pass
        await bot.send_photo(
            cb.message.chat.id,
            thumb_image,
            Presets.THUMB_CAPTION,
            reply_markup=reply_markup_del_thumb,
            parse_mode=enums.ParseMode.HTML
        )
    else:
        await cb.answer(Presets.NO_THUMB, show_alert=True)


@Client.on_callback_query(filters.regex(r'^thumb_del_conf_btn$'))
async def delete_thumb(bot: Client, cb: CallbackQuery):
    thumb_image_path = os.path.join(os.getcwd(), "thumbnails", f"{cb.from_user.id}.jpg")
    if os.path.exists(thumb_image_path):
        try:
            os.remove(thumb_image_path)
        except Exception:
            pass
        await cb.answer(Presets.DEL_THUMB_CNF, show_alert=True)
    else:
        await cb.answer(Presets.NO_THUMB, show_alert=True)
    try:
        await cb.message.delete()
        await cb.message.reply_text(
            Presets.OPTIONS_TXT,
            reply_markup=reply_markup_start,
            parse_mode=enums.ParseMode.HTML
        )
    except Exception:
        pass


@Client.on_callback_query(filters.regex(r'^help_btn$'))
async def help_bot(bot: Client, cb: CallbackQuery):
    await cb.answer()
    try:
        await cb.message.edit_text(
            Presets.HELP_TEXT,
            disable_web_page_preview=True,
            reply_markup=reply_markup_back,
            parse_mode=enums.ParseMode.HTML
        )
    except Exception:
        pass


@Client.on_callback_query(filters.regex(r'^back_btn$'))
async def back_button(bot: Client, cb: CallbackQuery):
    try:
        await cb.message.edit_text(
            Presets.OPTIONS_TXT,
            reply_markup=reply_markup_start,
            parse_mode=enums.ParseMode.HTML
        )
    except Exception:
        pass


@Client.on_callback_query(filters.regex(r'^cancel_btn$'))
async def cancel_upload_process(bot: Client, cb: CallbackQuery):
    user_id = cb.from_user.id
    cancel_process.pop(user_id, None)
    try:
        await cb.message.edit_text(
            Presets.CANCEL_PROCESS,
            parse_mode=enums.ParseMode.HTML
        )
        await asyncio.sleep(5)
        await cb.message.delete()
    except Exception:
        pass


@Client.on_callback_query()
async def youtube_dl_button_handler(bot: Client, cb: CallbackQuery):
    if "|" in cb.data:
        await youtube_dl_call_back(bot, cb)
