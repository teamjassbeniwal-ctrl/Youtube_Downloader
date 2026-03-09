import os
import asyncio
from pyrogram import Client
from pyrogram.errors import FloodWait
from pyrogram.types import InlineQuery, InlineQueryResultArticle, InputTextMessageContent
from presets import Presets
from library.info import get_info
from library.extract import youtube_search

if bool(os.environ.get("ENV", False)):
    from sample_config import Config
else:
    from config import Config


async def is_auth_inline(user_id: int):
    """Check if user is authorized for inline queries"""
    if Config.AUTH_USERS and (user_id not in Config.AUTH_USERS):
        return False
    return True


@Client.on_inline_query()
async def inline_search(bot: Client, query: InlineQuery):
    user_id = query.from_user.id
    results = []

    # Default info (bot info or some defaults)
    try:
        defaults = await get_info((await bot.get_me()).username)
        results.extend(defaults)
    except FloodWait as e:
        await asyncio.sleep(e.x)
    except Exception:
        pass

    # Auth check
    if not await is_auth_inline(user_id):
        try:
            await query.answer(
                results=results,
                switch_pm_text=Presets.NOT_AUTH_TXT,
                switch_pm_parameter="help"
            )
        except FloodWait as e:
            await asyncio.sleep(e.x)
        except Exception:
            pass
        return

    search_text = query.query.strip()
    if not search_text:
        try:
            await query.answer(results=results, cache_time=5)
        except Exception:
            pass
        return

    try:
        search_results = await youtube_search(search_text)
    except Exception:
        search_results = []

    for data in search_results:
        try:
            count = data.get('viewCount', {}).get('text', 'N/A')
            thumb = data.get('thumbnails', [{}])
            results.append(
                InlineQueryResultArticle(
                    title=(data.get('title', '')[:35] + "..") if len(data.get('title', '')) > 35 else data.get('title', ''),
                    input_message_content=InputTextMessageContent(
                        message_text=data.get('link', '')
                    ),
                    thumb_url=thumb[0].get('url', ''),
                    description=Presets.DESCRIPTION.format(data.get('duration', 'N/A'), count)
                )
            )
        except Exception:
            continue

    switch_pm_text = Presets.RESULTS_TXT if search_results else Presets.NO_RESULTS
    try:
        await query.answer(
            results=results,
            switch_pm_text=switch_pm_text,
            switch_pm_parameter="start"
        )
    except FloodWait as e:
        await asyncio.sleep(e.x)
    except Exception:
        pass
