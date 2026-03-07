from .general import *
import discord
from discord.ext import commands
import function as func

# settings.py


# Add additional settings or configuration variables below
APP_NAME = "Vocard"
DEBUG = True

class Settings(commands.Cog):
    """Các lệnh cài đặt và cấu hình"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.description = "Các lệnh quản lý cài đặt bot"

    # Add your settings commands here

async def setup(bot: commands.Bot):
    await bot.add_cog(Settings(bot))