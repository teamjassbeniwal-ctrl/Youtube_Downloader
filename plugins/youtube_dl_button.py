# Name     : Youtube_Downloader 'Inline' [ Telegram ]
# Repo     : https://github.com/Rexinazor/Youtube_Downloader
# Author   : Rexinazor

import os
import time
import json
import shutil
import asyncio
from datetime import datetime

from pyrogram.enums import ParseMode

from presets import Presets
from library.buttons import reply_markup_cancel
from library.buttons import reply_markup_join, reply_markup_close
from library.display_progress import cancel_process
from library.display_progress import progress_for_pyrogram, humanbytes

if bool(os.environ.get("ENV", False)):
    from sample_config import Config
else:
    from config import Config


async def youtube_dl_call_back(bot, m):

    user_id = int(m.from_user.id)
    cancel_process[user_id] = int(m.message.message_id)

    cb_data = m.data
    tg_send_type, youtube_dl_format, youtube_dl_ext = cb_data.split("|")

    base_dir = os.getcwd()

    thumb_image_path = os.path.join(base_dir, "thumbnails", f"{user_id}.jpg")
    yt_thumb_image_path = os.path.join(base_dir, "YThumb", f"{user_id}.jpg")
    save_ytdl_json_path = os.path.join(base_dir, "downloads", f"{user_id}.json")

    try:
        with open(save_ytdl_json_path, "r", encoding="utf8") as f:
            response_json = json.load(f)
    except FileNotFoundError:
        await bot.delete_messages(
            chat_id=m.message.chat.id,
            message_ids=m.message.message_id,
            revoke=True
        )
        return

    youtube_dl_url = m.message.reply_to_message.text
    custom_file_name = f"{response_json.get('title')}_{youtube_dl_format}.{youtube_dl_ext}"

    youtube_dl_username = None
    youtube_dl_password = None
    thumb_nail = None

    if "|" in youtube_dl_url:
        url_parts = youtube_dl_url.split("|")

        if len(url_parts) >= 2:
            youtube_dl_url = url_parts[0]
            custom_file_name = url_parts[1]

        if len(url_parts) == 4:
            youtube_dl_username = url_parts[2]
            youtube_dl_password = url_parts[3]

    await bot.edit_message_text(
        chat_id=m.message.chat.id,
        message_id=m.message.message_id,
        text=Presets.DOWNLOAD_START
    )

    description = Presets.CUSTOM_CAPTION_UL_FILE

    if "fulltitle" in response_json:
        description = response_json["fulltitle"][:1021] + "\n" + Presets.CUSTOM_CAPTION_UL_FILE

    user_download_dir = os.path.join(base_dir, "downloads", str(user_id))
    os.makedirs(user_download_dir, exist_ok=True)

    download_path = os.path.join(user_download_dir, custom_file_name)

    if tg_send_type == "audio":
        command = [
            "youtube-dl",
            "-c",
            "--max-filesize", str(Config.TG_MAX_FILE_SIZE),
            "--prefer-ffmpeg",
            "--extract-audio",
            "--audio-format", youtube_dl_ext,
            "--audio-quality", youtube_dl_format,
            youtube_dl_url,
            "-o", download_path
        ]
    else:
        format_code = youtube_dl_format

        if "youtu" in youtube_dl_url:
            format_code = youtube_dl_format + "+bestaudio"

        command = [
            "youtube-dl",
            "-c",
            "--max-filesize", str(Config.TG_MAX_FILE_SIZE),
            "--embed-subs",
            "-f", format_code,
            "--hls-prefer-ffmpeg",
            youtube_dl_url,
            "-o", download_path
        ]

    if Config.HTTP_PROXY:
        command += ["--proxy", Config.HTTP_PROXY]

    if youtube_dl_username:
        command += ["--username", youtube_dl_username]

    if youtube_dl_password:
        command += ["--password", youtube_dl_password]

    command.append("--no-warnings")

    if "hotstar" in youtube_dl_url:
        command += ["--geo-bypass-country", "IN"]

    process = await asyncio.create_subprocess_exec(
        *command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    stdout, stderr = await process.communicate()

    error_response = stderr.decode().strip()

    if error_response:
        if Presets.AD_STRING_TO_REPLACE in error_response:
            error_response = error_response.replace(Presets.AD_STRING_TO_REPLACE, "")

        await bot.edit_message_text(
            chat_id=m.message.chat.id,
            message_id=m.message.message_id,
            text=error_response
        )
        return

    try:
        file_size = os.stat(download_path).st_size
    except:
        await bot.edit_message_text(
            chat_id=m.message.chat.id,
            message_id=m.message.message_id,
            text=Presets.LINK_ERROR,
            reply_markup=reply_markup_close
        )
        return

    if file_size > Config.TG_MAX_FILE_SIZE:

        await bot.edit_message_text(
            chat_id=m.message.chat.id,
            message_id=m.message.message_id,
            text=Presets.RCHD_TG_API_LIMIT.format(humanbytes(file_size))
        )
        return

    await bot.edit_message_text(
        chat_id=m.message.chat.id,
        message_id=m.message.message_id,
        text=Presets.UPLOAD_START,
        reply_markup=reply_markup_cancel
    )

    if os.path.exists(thumb_image_path):
        thumb_nail = thumb_image_path
    elif os.path.exists(yt_thumb_image_path):
        thumb_nail = yt_thumb_image_path

    start_time = time.time()

    if user_id not in cancel_process:
        return

    try:

        if tg_send_type == "audio":

            await bot.send_audio(
                chat_id=m.message.chat.id,
                audio=download_path,
                caption=description,
                parse_mode=ParseMode.HTML,
                thumb=thumb_nail,
                reply_markup=reply_markup_join,
                progress=progress_for_pyrogram,
                progress_args=(
                    Presets.UPLOAD_START,
                    m.message,
                    start_time,
                    bot,
                    user_id
                )
            )

        elif tg_send_type == "file":

            await bot.send_document(
                chat_id=m.message.chat.id,
                document=download_path,
                caption=description,
                thumb=thumb_nail,
                parse_mode=ParseMode.HTML,
                reply_markup=reply_markup_join,
                reply_to_message_id=m.message.reply_to_message.message_id,
                progress=progress_for_pyrogram,
                progress_args=(
                    Presets.UPLOAD_START,
                    m.message,
                    start_time,
                    bot,
                    user_id
                )
            )

        elif tg_send_type == "video":

            await bot.send_video(
                chat_id=m.message.chat.id,
                video=download_path,
                caption=description,
                parse_mode=ParseMode.HTML,
                supports_streaming=True,
                thumb=thumb_nail,
                reply_markup=reply_markup_join,
                reply_to_message_id=m.message.reply_to_message.message_id,
                progress=progress_for_pyrogram,
                progress_args=(
                    Presets.UPLOAD_START,
                    m.message,
                    start_time,
                    bot,
                    user_id
                )
            )

    except Exception as e:

        await bot.send_message(
            m.message.chat.id,
            f"Upload Failed\n\n{e}"
        )

    try:
        shutil.rmtree(user_download_dir)
    except:
        pass

    await bot.delete_messages(
        m.message.chat.id,
        m.message.message_id
    )
