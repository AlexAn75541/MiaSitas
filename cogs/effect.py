"""MIT License

Copyright (c) 2023 - present Vocard Development

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import discord
import voicelink

from function import (
    send,
    get_lang,
    get_aliases,
    cooldown_check
)
from discord import app_commands
from discord.ext import commands


async def check_access(ctx: commands.Context):
    player: voicelink.Player = ctx.guild.voice_client
    if not player:
        text = await get_lang(ctx.guild.id, "noPlayer")
        raise voicelink.exceptions.VoicelinkException(text)

    if ctx.author not in player.channel.members:
        if not ctx.author.guild_permissions.manage_guild:
            text = await get_lang(ctx.guild.id, "notInChannel")
            raise voicelink.exceptions.VoicelinkException(text.format(ctx.author.mention, player.channel.mention))

    return player

class Effect(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.description = "Đây là mục hiệu ứng bài hát chỉ dành cho DJ trong kênh thoại server. (Có thể chỉnh dj với lệnh /settings setdj <VAI TRÒ DJ>)"

    async def effect_autocomplete(self, interaction: discord.Interaction, current: str) -> list:
        player: voicelink.Player = interaction.guild.voice_client
        if not player:
            return []
        if current:
            return [app_commands.Choice(name=effect.tag, value=effect.tag) for effect in player.filters.get_filters() if current in effect.tag]
        return [app_commands.Choice(name=effect.tag, value=effect.tag) for effect in player.filters.get_filters()]

    @commands.hybrid_command(name="speed", aliases=get_aliases("speed"))
    @app_commands.describe(value="Chỉnh tốc độ phát nhạc. Mặc định là `1.0`")
    @commands.dynamic_cooldown(cooldown_check, commands.BucketType.guild)
    async def speed(self, ctx: commands.Context, value: commands.Range[float, 0, 2]):
        """Chỉnh tốc độ phát nhạc."""
        player = await check_access(ctx)

        if player.filters.has_filter(filter_tag="speed"):
            player.filters.remove_filter(filter_tag="speed")

        effect = voicelink.Timescale(tag="speed", speed=value)
        await player.add_filter(effect, ctx.author)
        await send(ctx, "addEffect", effect.tag)

    @commands.hybrid_command(name="karaoke", aliases=get_aliases("karaoke"))
    @app_commands.describe(
        level="Mức độ của karaoke. Mặc định là `1.0`",
        monolevel="Mức độ mono của karaoke. Mặc định là `1.0`",
        filterband="Bộ lọc băng tần(?) của karaoke. Mặc định là `220.0`",
        filterwidth="Chiều rộng bộ lọc(?) của karaoke. Mặc định là `100.0`"
    )
    @commands.dynamic_cooldown(cooldown_check, commands.BucketType.guild)
    async def karaoke(self, ctx: commands.Context, level: commands.Range[float, 0, 2] = 1.0, monolevel: commands.Range[float, 0, 2] = 1.0, filterband: commands.Range[float, 100, 300] = 220.0, filterwidth: commands.Range[float, 50, 150] = 100.0) -> None:
        """Thêm hiệu ứng karaoke vào bài nhạc đang được phát của bạn."""
        player = await check_access(ctx)

        if player.filters.has_filter(filter_tag="karaoke"):
            player.filters.remove_filter(filter_tag="karaoke")

        effect = voicelink.Karaoke(tag="karaoke", level=level, mono_level=monolevel, filter_band=filterband, filter_width=filterwidth)
        await player.add_filter(effect, ctx.author)
        await send(ctx, "addEffect", effect.tag)

    @commands.hybrid_command(name="tremolo", aliases=get_aliases("tremolo"))
    @app_commands.describe(
        frequency="Mức độ tần số của tremolo. Mặc định là `2.0`",
        depth="Độ sâu của tremolo. Mặc định là `0.5`"
    )
    @commands.dynamic_cooldown(cooldown_check, commands.BucketType.guild)
    async def tremolo(self, ctx: commands.Context, frequency: commands.Range[float, 0, 10] = 2.0, depth: commands.Range[float, 0, 1] = 0.5) -> None:
        """Thêm tremolo vào player của bạn. Tremolo là một hiệu ứng âm thanh làm thay đổi âm lượng theo tần số."""
        player = await check_access(ctx)

        if player.filters.has_filter(filter_tag="tremolo"):
            player.filters.remove_filter(filter_tag="tremolo")

        effect = voicelink.Tremolo(tag="tremolo", frequency=frequency, depth=depth)
        await player.add_filter(effect, ctx.author)
        await send(ctx, "addEffect", effect.tag)

    @commands.hybrid_command(name="vibrato", aliases=get_aliases("vibrato"))
    @app_commands.describe(
        frequency="Tần số của vibrato. Mặc định là `2.0`",
        depth="Độ sâu của vibrato. Mặc định là `0.5`"
    )
    @commands.dynamic_cooldown(cooldown_check, commands.BucketType.guild)
    async def vibrato(self, ctx: commands.Context, frequency: commands.Range[float, 0, 14] = 2.0, depth: commands.Range[float, 0, 1] = 0.5) -> None:
        """Cũng giống như tremolo, nhưng thay đổi tần số thay vì âm lượng."""
        player = await check_access(ctx)

        if player.filters.has_filter(filter_tag="vibrato"):
            player.filters.remove_filter(filter_tag="vibrato")

        effect = voicelink.Vibrato(tag="vibrato", frequency=frequency, depth=depth)
        await player.add_filter(effect, ctx.author)
        await send(ctx, "addEffect", effect.tag)

    @commands.hybrid_command(name="rotation", aliases=get_aliases("rotation"))
    @app_commands.describe(hertz="Tần số của hiệu ứng xoay. Mặc định là `0.2`")
    @commands.dynamic_cooldown(cooldown_check, commands.BucketType.guild)
    async def rotation(self, ctx: commands.Context, hertz: commands.Range[float, 0, 2] = 0.2) -> None:
        """Làm xoay âm thanh theo tần số. Hiệu ứng này có thể tạo ra âm thanh rất thú vị."""
        player = await check_access(ctx)

        if player.filters.has_filter(filter_tag="rotation"):
            player.filters.remove_filter(filter_tag="rotation")

        effect = voicelink.Rotation(tag="rotation", rotation_hertz=hertz)
        await player.add_filter(effect, ctx.author)
        await send(ctx, "addEffect", effect.tag)

    @commands.hybrid_command(name="distortion", aliases=get_aliases("distortion"))
    @commands.dynamic_cooldown(cooldown_check, commands.BucketType.guild)
    async def distortion(self, ctx: commands.Context) -> None:
        """Tạo ra hiệu ứng méo tiếng."""
        player = await check_access(ctx)

        if player.filters.has_filter(filter_tag="distortion"):
            player.filters.remove_filter(filter_tag="distortion")

        effect = voicelink.Distortion(tag="distortion", sin_offset=0.0, sin_scale=1.0, cos_offset=0.0, cos_scale=1.0, tan_offset=0.0, tan_scale=1.0, offset=0.0, scale=1.0)
        await player.add_filter(effect, ctx.author)
        await send(ctx, "addEffect", effect.tag)

    @commands.hybrid_command(name="lowpass", aliases=get_aliases("lowpass"))
    @app_commands.describe(smoothing="Mức độ làm mượt của bộ lọc(lowPass). Mặc định là `20.0` (giá trị từ `10` đến `30`)")
    @commands.dynamic_cooldown(cooldown_check, commands.BucketType.guild)
    async def lowpass(self, ctx: commands.Context, smoothing: commands.Range[float, 10, 30] = 20.0) -> None:
        """Bộ lọc âm thanh thấp(lowPass)."""
        player = await check_access(ctx)

        if player.filters.has_filter(filter_tag="lowpass"):
            player.filters.remove_filter(filter_tag="lowpass")

        effect = voicelink.LowPass(tag="lowpass", smoothing=smoothing)
        await player.add_filter(effect, ctx.author)
        await send(ctx, "addEffect", effect.tag)

    @commands.hybrid_command(name="channelmix", aliases=get_aliases("channelmix"))
    @app_commands.describe(
        left_to_left="Tiếng từ trái sang trái. Mặc định là `1.0`",
        right_to_right="Tiếng từ phải sang phải. Mặc định là `1.0`",
        left_to_right="Tiếng từ trái sang phải. Mặc định là `0.0`",
        right_to_left="Tiếng từ phải sang trái. Mặc định là `0.0`"
    )
    @commands.dynamic_cooldown(cooldown_check, commands.BucketType.guild)
    async def channelmix(self, ctx: commands.Context, left_to_left: commands.Range[float, 0, 1] = 1.0, right_to_right: commands.Range[float, 0, 1] = 1.0, left_to_right: commands.Range[float, 0, 1] = 0.0, right_to_left: commands.Range[float, 0, 1] = 0.0) -> None:
        """Bộ lọc trộn kênh âm thanh(channelMix)."""
        player = await check_access(ctx)

        if player.filters.has_filter(filter_tag="channelmix"):
            player.filters.remove_filter(filter_tag="channelmix")

        effect = voicelink.ChannelMix(tag="channelmix", left_to_left=left_to_left, right_to_right=right_to_right, left_to_right=left_to_right, right_to_left=right_to_left)
        await player.add_filter(effect, ctx.author)
        await send(ctx, "addEffect", effect.tag)

    @commands.hybrid_command(name="nightcore", aliases=get_aliases("nightcore"))
    @commands.dynamic_cooldown(cooldown_check, commands.BucketType.guild)
    async def nightcore(self, ctx: commands.Context) -> None:
        """Thêm hiệu ứng Nightcore vào player của bạn."""       
        player = await check_access(ctx)
        effect = voicelink.Timescale.nightcore()
        await player.add_filter(effect, ctx.author)
        await send(ctx, "addEffect", effect.tag)

    @commands.hybrid_command(name="8d", aliases=get_aliases("8d"))
    @commands.dynamic_cooldown(cooldown_check, commands.BucketType.guild)
    async def eightD(self, ctx: commands.Context) -> None:
        """Thêm hiệu ứng 8D vào player của bạn."""
        player = await check_access(ctx)

        effect = voicelink.Rotation.nightD()
        await player.add_filter(effect, ctx.author)
        await send(ctx, "addEffect", effect.tag)

    @commands.hybrid_command(name="vaporwave", aliases=get_aliases("vaporwave"))
    @commands.dynamic_cooldown(cooldown_check, commands.BucketType.guild)
    async def vaporwave(self, ctx: commands.Context) -> None:
        """Thêm hiệu ứng Vaporwave vào player của bạn."""
        player = await check_access(ctx)

        effect = voicelink.Timescale.vaporwave()
        await player.add_filter(effect, ctx.author)
        await send(ctx, "addEffect", effect.tag)

    @commands.hybrid_command(name="cleareffect", aliases=get_aliases("cleareffect"))
    @app_commands.describe(effect="Remove a specific sound effects.")
    @app_commands.autocomplete(effect=effect_autocomplete)
    @commands.dynamic_cooldown(cooldown_check, commands.BucketType.guild)
    async def cleareffect(self, ctx: commands.Context, effect: str = None) -> None:
        """Giúp bạn xóa hiệu ứng âm thanh khỏi player của bạn."""
        player = await check_access(ctx)

        if effect:
            await player.remove_filter(effect)
        else:
            await player.reset_filter()
            
        await send(ctx, "clearEffect")

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Effect(bot))
