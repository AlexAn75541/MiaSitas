import discord
from discord.ext import commands
import function as func
import psutil
import platform
from datetime import datetime
from discord import app_commands  # Add this import

class General(commands.Cog):
    """General purpose commands for server management and utility"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.description = "General purpose commands for everyday use"

    @app_commands.command(name="serverinfo", description="Get information about the server")  # Use app_commands instead
    async def serverinfo(self, interaction: discord.Interaction):  # Change to interaction
        """Get information about the server"""
        guild = interaction.guild
        embed = discord.Embed(title=f"{guild.name} Info", color=func.settings.embed_color)
        
        # Add server info fields
        embed.add_field(name="Owner", value=guild.owner.mention, inline=True)
        embed.add_field(name="Created At", value=guild.created_at.strftime("%Y-%m-%d"), inline=True)
        embed.add_field(name="Member Count", value=guild.member_count, inline=True)
        embed.add_field(name="Channels", value=f"Text: {len(guild.text_channels)}\nVoice: {len(guild.voice_channels)}", inline=True)
        embed.add_field(name="Roles", value=len(guild.roles), inline=True)
        embed.add_field(name="Boost Level", value=guild.premium_tier, inline=True)
        
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
            
        await interaction.response.send_message(embed=embed)

    @commands.hybrid_command(name="latency")  # Changed from ping to latency
    async def ping(self, ctx: commands.Context):
        """Check bot's latency"""
        start = datetime.now()
        msg = await ctx.send("Pinging...")
        end = datetime.now()
        
        latency = (end - start).total_seconds() * 1000
        await msg.edit(content=f"Pong! 🏓\nBot Latency: {latency:.2f}ms\nWebsocket Latency: {self.bot.latency * 1000:.2f}ms")

    @commands.hybrid_command()
    async def botinfo(self, ctx: commands.Context):
        """Get information about the bot"""
        embed = discord.Embed(title="Bot Information", color=func.settings.embed_color)
        
        # System info
        memory = psutil.virtual_memory()
        embed.add_field(name="System", 
                       value=f"Python: {platform.python_version()}\n"
                             f"Discord.py: {discord.__version__}\n"
                             f"Memory: {memory.percent}%\n"
                             f"CPU: {psutil.cpu_percent()}%", 
                       inline=False)
        
        # Bot stats
        embed.add_field(name="Stats",
                       value=f"Servers: {len(self.bot.guilds)}\n"
                             f"Users: {sum(g.member_count for g in self.bot.guilds)}\n"
                             f"Commands: {len(self.bot.commands)}\n"
                             f"Uptime: {datetime.now() - self.bot.uptime}", 
                       inline=False)
        
        await ctx.send(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(General(bot))