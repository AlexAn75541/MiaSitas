import discord
import function as func
import voicelink

from voicelink.config import Config
from discord.ext import commands, tasks

class Task(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

        self.activity_update.start()
        self.cache_cleaner.start()

        self.current_act = 0

    def cog_unload(self):
        self.activity_update.cancel()
        self.cache_cleaner.cancel()
    
    @tasks.loop(seconds=Config().timer_settings.get("bot_activity_update", 600))
    async def activity_update(self):
        act = Config().activity
        if not act:
            return

        if self.current_act >= len(act):
            self.current_act = 0

        try:
            act_type, act_name = act[self.current_act]
            await self.bot.change_presence(activity=discord.Activity(type=discord.ActivityType[act_type], name=act_name))
            self.current_act += 1
            if Config().logging.get("enable", False):
                func.logger.info(f"Chỉnh bot sang hoạt động {act_name}")

        except Exception as e:
            func.logger.error("Đã có lỗi trong quá trình chuyển hoạt động", exc_info=e)

    @tasks.loop(seconds=Config().timer_settings.get("cache_cleanup", 43200))
    async def cache_cleaner(self):
        await voicelink.MongoDBHandler.cleanup_cache()

async def setup(bot: commands.Bot):
    await bot.add_cog(Task(bot))
