# Name     : Youtube_Downloader 'Inline' [ Telegram ]
# Repo     : https://github.com/Rexinazor/Youtube_Downloader
# Author   : Rexinazor

import os
import re
import wget
import json
import asyncio
from presets import Presets
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from pyrogram.enums import ParseMode

from library.extract import yt_link_search
from library.display_progress import humanbytes

# Load config
if bool(os.environ.get("ENV", False)):
    from sample_config import Config
else:
    from config import Config

ytregex = r"^((?:https?:)?\/\/)?((?:www|m)\.)?((?:youtube\.com|youtu.be))(\/(?:[\w\-]+\?v=|embed\/|v\/)?)([\w\-]+)(\S+)?$"


@Client.on_message(filters.private & filters.regex(ytregex))
async def echo(bot, m: Message):
    # Check authorized users
    if Config.AUTH_USERS and (m.from_user.id not in Config.AUTH_USERS):
        await m.reply_text(
            Presets.NOT_AUTH_TXT,
            reply_to_message_id=m.id
        )
        return

    msg = await m.reply_text(text=Presets.CHECKING_LINK, quote=True)
    url = m.text
    youtube_dl_username = None
    youtube_dl_password = None
    file_name = None

    # Parse custom file_name / credentials
    if "|" in url:
        url_parts = url.split("|")
        if len(url_parts) == 2:
            url = url_parts[0].strip()
            file_name = url_parts[1].strip()
        elif len(url_parts) == 4:
            url = url_parts[0].strip()
            file_name = url_parts[1].strip()
            youtube_dl_username = url_parts[2].strip()
            youtube_dl_password = url_parts[3].strip()
        else:
            for entity in m.entities or []:
                if entity.type == "text_link":
                    url = entity.url
                elif entity.type == "url":
                    o = entity.offset
                    ln = entity.length
                    url = url[o:o + ln]
    else:
        for entity in m.entities or []:
            if entity.type == "text_link":
                url = entity.url
            elif entity.type == "url":
                o = entity.offset
                ln = entity.length
                url = url[o:o + ln]

    # Prepare youtube-dl command
    command_to_exec = [
        "youtube-dl",
        "--no-warnings",
        "--youtube-skip-dash-manifest",
        "-j",
        url
    ]

    if Config.HTTP_PROXY:
        command_to_exec.extend(["--proxy", Config.HTTP_PROXY])

    if "hotstar" in url:
        command_to_exec.extend(["--geo-bypass-country", "IN"])

    if youtube_dl_username:
        command_to_exec.extend(["--username", youtube_dl_username])
    if youtube_dl_password:
        command_to_exec.extend(["--password", youtube_dl_password])

    process = await asyncio.create_subprocess_exec(
        *command_to_exec,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await process.communicate()
    e_response = stderr.decode().strip()
    t_response = stdout.decode().strip()

    # Error handling
    if e_response and "nonnumeric port" not in e_response:
        error_message = e_response.replace(Presets.AD_STRING_TO_REPLACE, "")
        if "This video is only available for registered users." in error_message:
            error_message += Presets.SET_CUSTOM_USERNAME_PASSWORD
        await bot.send_message(
            chat_id=m.chat.id,
            text=Presets.NO_VOID_FORMAT_FOUND.format(str(error_message)),
            reply_to_message_id=m.id,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True
        )
        return False

    # Process youtube-dl response
    if t_response:
        x_response = t_response.split("\n")[0]
        response_json = json.loads(x_response)

        json_path = os.path.join(os.getcwd(), "downloads")
        os.makedirs(json_path, exist_ok=True)
        save_ytdl_json_path = os.path.join(json_path, f"{m.from_user.id}.json")

        with open(save_ytdl_json_path, "w", encoding="utf8") as outfile:
            json.dump(response_json, outfile, ensure_ascii=False)

        inline_keyboard = []
        duration = response_json.get("duration")

        if "formats" in response_json:
            for formats in response_json["formats"]:
                format_id = formats.get("format_id")
                format_string = formats.get("format_note") or formats.get("format")
                format_ext = formats.get("ext")
                approx_file_size = humanbytes(formats["filesize"]) if "filesize" in formats else ""

                cb_string_video = f"video|{format_id}|{format_ext}"
                cb_string_file = f"file|{format_id}|{format_ext}"

                if format_string and "audio only" not in format_string.lower():
                    ikeyboard = [
                        InlineKeyboardButton(
                            f"S {format_string} video {approx_file_size} ",
                            callback_data=cb_string_video
                        ),
                        InlineKeyboardButton(
                            f"D {format_ext} {approx_file_size} ",
                            callback_data=cb_string_file
                        )
                    ]
                else:
                    ikeyboard = [
                        InlineKeyboardButton(
                            f"SVideo [ ] ( {approx_file_size} )",
                            callback_data=cb_string_video
                        ),
                        InlineKeyboardButton(
                            f"DFile [ ] ( {approx_file_size} )",
                            callback_data=cb_string_file
                        )
                    ]
                inline_keyboard.append(ikeyboard)

            # Add MP3 options if duration exists
            if duration:
                inline_keyboard.append([
                    InlineKeyboardButton("🎶MP3🎶 (64 kbps)", callback_data="audio|64k|mp3"),
                    InlineKeyboardButton("🎶MP3🎶 (128 kbps)", callback_data="audio|128k|mp3")
                ])
                inline_keyboard.append([
                    InlineKeyboardButton("🎶MP3🎶 (320 kbps)", callback_data="audio|320k|mp3")
                ])
        else:
            format_id = response_json["format_id"]
            format_ext = response_json["ext"]
            cb_string_video = f"video|{format_id}|{format_ext}"
            cb_string_file = f"file|{format_id}|{format_ext}"
            inline_keyboard.append([
                InlineKeyboardButton("🎞️SVideo🎞️", callback_data=cb_string_video),
                InlineKeyboardButton("🗂️DFile🗂️", callback_data=cb_string_file)
            ])

        reply_markup = InlineKeyboardMarkup(inline_keyboard)

        # Thumbnail
        yt_thumb_dir = os.path.join(os.getcwd(), "YThumb")
        os.makedirs(yt_thumb_dir, exist_ok=True)
        yt_thumb_image_path = os.path.join(yt_thumb_dir, f"{m.from_user.id}.jpg")

        try:
            if os.path.exists(yt_thumb_image_path):
                os.remove(yt_thumb_image_path)
        except:
            pass

        try:
            result = await yt_link_search(url)
            views = result['viewCount']['text']
            title = result['title'][:25] + ".."
            link = result['channel']['link']
            channel = result['channel']['name']
            rating = round(result['averageRating'], 1)
            uploaded_date = result['uploadDate']

            exp = r"^.*((youtu.be\/)|(v\/)|(\/u\/\w\/)|(embed\/)|(watch\?))\??v?=?([^#&?]*).*"
            sx = re.findall(exp, url)[0][-1]
            thumb = f"https://i.ytimg.com/vi/{sx}/maxresdefault.jpg"
            wget.download(thumb, yt_thumb_image_path, bar=None)
        except:
            await msg.edit(Presets.NOT_DOWNLOADABLE)
            await m.delete()
            await asyncio.sleep(5)
            await msg.delete()
            return

        await msg.delete()
        await m.reply_photo(
            photo=thumb,
            caption=Presets.FORMAT_SELECTION.format(
                title, link, channel, uploaded_date, views, rating
            ),
            reply_to_message_id=m.id,
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
                )
