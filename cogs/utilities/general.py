import discord
from discord.ext import commands
import function as func
import psutil
import platform
from datetime import datetime
from discord import app_commands  # Add this import

class General(commands.Cog):
    """Các lệnh chung cho quản lý máy chủ và tiện ích"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.description = "Các lệnh tiện ích cho sử dụng hàng ngày"

    @app_commands.command(name="serverinfo", description="Xem thông tin về máy chủ")  # Use app_commands instead
    async def serverinfo(self, interaction: discord.Interaction):  # Change to interaction
        """Xem thông tin về máy chủ"""
        guild = interaction.guild
        embed = discord.Embed(title=f"Thông tin {guild.name}", color=func.settings.embed_color)
        
        # Add server info fields
        embed.add_field(name="Chủ sở hữu", value=guild.owner.mention, inline=True)
        embed.add_field(name="Ngày tạo", value=guild.created_at.strftime("%Y-%m-%d"), inline=True)
        embed.add_field(name="Số thành viên", value=guild.member_count, inline=True)
        embed.add_field(name="Kênh", value=f"Văn bản: {len(guild.text_channels)}\nThoại: {len(guild.voice_channels)}", inline=True)
        embed.add_field(name="Vai trò", value=len(guild.roles), inline=True)
        embed.add_field(name="Cấp Boost", value=guild.premium_tier, inline=True)
        
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
            
        await interaction.response.send_message(embed=embed)

    @commands.hybrid_command(name="latency")  # Changed from ping to latency
    async def ping(self, ctx: commands.Context):
        """Kiểm tra độ trễ của bot"""
        start = datetime.now()
        msg = await ctx.send("Đang kiểm tra...")
        end = datetime.now()
        
        latency = (end - start).total_seconds() * 1000
        await msg.edit(content=f"Pong! 🏓\nĐộ trễ Bot: {latency:.2f}ms\nĐộ trễ Websocket: {self.bot.latency * 1000:.2f}ms")

    @commands.hybrid_command()
    async def botinfo(self, ctx: commands.Context):
        """Xem thông tin về bot"""
        embed = discord.Embed(title="Thông tin Bot", color=func.settings.embed_color)
        
        # System info
        memory = psutil.virtual_memory()
        embed.add_field(name="Hệ thống", 
                       value=f"Python: {platform.python_version()}\n"
                             f"Discord.py: {discord.__version__}\n"
                             f"Bộ nhớ: {memory.percent}%\n"
                             f"CPU: {psutil.cpu_percent()}%", 
                       inline=False)
        
        # Bot stats
        embed.add_field(name="Thống kê",
                       value=f"Máy chủ: {len(self.bot.guilds)}\n"
                             f"Người dùng: {sum(g.member_count for g in self.bot.guilds)}\n"
                             f"Lệnh: {len(self.bot.commands)}\n"
                             f"Thời gian hoạt động: {datetime.now() - self.bot.uptime}", 
                       inline=False)
        
        await ctx.send(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(General(bot))