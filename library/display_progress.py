# Name     : Youtube_Downloader 'Inline' [ Telegram ]
# Repo     : https://github.com/Rexinazor/Youtube_Downloader
# Author   : Rexinazor

import math
import time
from presets import Presets
from library.buttons import reply_markup_cancel

cancel_process = {}

async def progress_for_pyrogram(
    current,
    total,
    ud_type,
    message,
    start,
    bot,
    id
):
    now = time.time()
    diff = now - start
    if round(diff % 10.00) == 0 or current == total:
        percentage = current * 100 / total
        speed = current / diff if diff > 0 else 0
        elapsed_time_ms = round(diff) * 1000
        time_to_completion_ms = round((total - current) / speed) * 1000 if speed > 0 else 0
        estimated_total_time_ms = elapsed_time_ms + time_to_completion_ms

        elapsed_time_str = TimeFormatter(milliseconds=elapsed_time_ms)
        estimated_total_time_str = TimeFormatter(milliseconds=estimated_total_time_ms)

        progress_bar = "{0}{1}\nStatus   : {2}%\n".format(
            ''.join([Presets.FINISHED_PROGRESS_STR for _ in range(math.floor(percentage / 7.6923))]),
            ''.join([Presets.UN_FINISHED_PROGRESS_STR for _ in range(13 - math.floor(percentage / 7.6923))]),
            round(percentage, 2)
        )

        progress_text = progress_bar + "Process : {0}  𝐎𝐟  {1}\nSpeed    : {2}/s\nWaiting : {3}\n".format(
            humanbytes(current),
            humanbytes(total),
            humanbytes(speed),
            estimated_total_time_str if estimated_total_time_str else "0 s"
        )

        try:
            await message.edit(
                text="{}\n{}".format(ud_type, progress_text),
                reply_markup=reply_markup_cancel
            )
        except Exception:
            pass

    # Stop if user canceled
    if id not in cancel_process:
        # Instead of bot.stop_transmission(), just pass
        return


def humanbytes(size):
    if not size:
        return ""
    power = 2**10
    n = 0
    Dic_powerN = {0: ' ', 1: 'Ki', 2: 'Mi', 3: 'Gi', 4: 'Ti'}
    while size > power:
        size /= power
        n += 1
    return str(round(size, 2)) + " " + Dic_powerN[n] + 'B'


def TimeFormatter(milliseconds: int) -> str:
    seconds, milliseconds = divmod(int(milliseconds), 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    tmp = ((str(days) + "d, ") if days else "") + \
          ((str(hours) + "h, ") if hours else "") + \
          ((str(minutes) + "m, ") if minutes else "") + \
          ((str(seconds) + "s, ") if seconds else "") + \
          ((str(milliseconds) + "ms, ") if milliseconds else "")
    return tmp[:-2]
