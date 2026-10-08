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
            item = act[self.current_act]
            if isinstance(item, dict):
                act_type_name = str(item.get("type", "playing")).lower()
                act_name = item.get("name")
                status_name = str(item.get("status", "online")).lower()
            elif isinstance(item, (list, tuple)) and len(item) >= 2:
                act_type_name = str(item[0]).lower()
                act_name = str(item[1])
                status_name = str(item[2]).lower() if len(item) > 2 else "online"
            else:
                act_type_name = "playing"
                act_name = str(item)
                status_name = "online"

            type_map = {
                "play": "playing",
                "listen": "listening",
                "watch": "watching",
                "stream": "streaming",
                "compete": "competing",
            }
            act_type_name = type_map.get(act_type_name, act_type_name)
            act_type = getattr(discord.ActivityType, act_type_name, discord.ActivityType.playing)
            status = getattr(discord.Status, status_name, discord.Status.online)

            if act_name:
                await self.bot.change_presence(activity=discord.Activity(type=act_type, name=act_name), status=status)
                if Config().logging.get("enable", False):
                    func.logger.info(f"Chỉnh bot sang hoạt động {act_name}")

            self.current_act += 1

        except Exception as e:
            func.logger.error("Đã có lỗi trong quá trình chuyển hoạt động", exc_info=e)

    @tasks.loop(seconds=Config().timer_settings.get("cache_cleanup", 43200))
    async def cache_cleaner(self):
        await voicelink.MongoDBHandler.cleanup_cache()

async def setup(bot: commands.Bot):
    await bot.add_cog(Task(bot))
