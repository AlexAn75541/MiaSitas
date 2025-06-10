import discord
from discord.ext import commands
import function as func

class General(commands.Cog):
    """General purpose commands for server management and utility"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.description = "General purpose commands for everyday use"

    @commands.hybrid_command()
    async def serverinfo(self, ctx: commands.Context):
        """Get information about the server"""
        guild = ctx.guild
        embed = discord.Embed(title=f"{guild.name} Info", color=func.settings.embed_color)
        # Add server info fields
        await ctx.send(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(General(bot))