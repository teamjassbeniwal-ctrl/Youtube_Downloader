import os
import asyncio
from pyrogram import Client, enums  # ✅ import enums
from aiohttp import web

# Config
if bool(os.environ.get("ENV", False)):
    from sample_config import Config, LOGGER
else:
    from config import Config, LOGGER

# Web server handler
async def handle(request):
    return web.Response(text="Bot is alive!")

class Bot(Client):
    def __init__(self):
        super().__init__(
            "bot",
            bot_token=Config.TG_BOT_TOKEN,
            api_id=Config.APP_ID,
            api_hash=Config.API_HASH,
            plugins={"root": "plugins"},
            parse_mode=enums.ParseMode.HTML  # ✅ Set HTML globally here
        )
        self.LOGGER = LOGGER

    async def start(self):
        await super().start()
        me = await self.get_me()
        self.LOGGER(__name__).info(f"@{me.username} started!")

        # Start HTTP server for health check in background
        self.app = web.Application()
        self.app.add_routes([web.get("/", handle)])
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        self.site = web.TCPSite(self.runner, "0.0.0.0", 5000)
        await self.site.start()
        self.LOGGER(__name__).info("HTTP server running on port 5000")

    async def stop(self, *args):
        # Stop HTTP server
        if hasattr(self, "runner"):
            await self.runner.cleanup()
        await super().stop()
        self.LOGGER(__name__).info("Bot stopped. Bye.")

# Run bot
if __name__ == "__main__":
    app = Bot()
    app.run()
