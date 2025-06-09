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
from discord.ext import commands

import function as func

class HelpDropdown(discord.ui.Select):
    def __init__(self, categories: list):
        self.categories = categories  # Store categories for later use
        
        options = [
            discord.SelectOption(
                emoji="🆕",
                label="Thông tin",
                description="Xem thông tin của bot MiaSitas(Vocard Fork)"
            ),
            discord.SelectOption(
                emoji="🕹️",
                label="Hướng dẫn",
                description="Cách để sử dụng bot."
            ),
        ]
        
        # Add command categories
        for category, emoji in zip(categories, ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣"]):
            options.append(
                discord.SelectOption(
                    emoji=emoji,
                    label=f"Các lệnh {category}",
                    description=f"Đây là mục chứa những lệnh {category.lower()}"
                )
            )

        super().__init__(
            placeholder="Chọn một mục nào đó...",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="select"
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        if not interaction.user == self.view.author:
            await interaction.response.send_message("Bạn không thể gửi tin nhắn này", ephemeral=True)
            return

        try:
            selected_value = self.values[0]
            
            if selected_value == "Tin tức":
                category = "news"
            elif selected_value == "Hướng dẫn":
                category = "tutorial"
            else:
                category = selected_value.replace("Các lệnh ", "")
            
            embed = self.view.build_embed(category)
            
            await interaction.response.edit_message(embed=embed)
            
        except Exception as e:
            func.logger.error(f"Failed to send error message: {e}")
            
class HelpView(discord.ui.View):
    def __init__(self, bot: commands.Bot, author: discord.Member) -> None:
        super().__init__(timeout=60)

        self.author: discord.Member = author
        self.bot: commands.Bot = bot
        self.response: discord.Message = None
        self.categories: list[str] = [ name.capitalize() for name, cog in bot.cogs.items() if len([c for c in cog.walk_commands()]) ]

        self.add_item(discord.ui.Button(label='Website của bot Vocard', emoji='🌎', url='https://vocard.xyz'))
        self.add_item(discord.ui.Button(label='Vocard Discord Server', emoji=':support:915152950471581696', url='https://discord.gg/WYDrzHt2uk'))
        # self.add_item(discord.ui.Button(label='Github', emoji=':github:1098265017268322406', url='https://github.com/ChocoMeow/Vocard'))
        # self.add_item(discord.ui.Button(label='Donate', emoji=':patreon:913397909024800878', url='https://www.patreon.com/Vocard'))
        self.add_item(HelpDropdown(self.categories))
    
    async def on_error(self, error, item, interaction) -> None:
            func.logger.error(f"Failed to send error message: {str(e)}")

    async def on_timeout(self) -> None:
        for child in self.children:
            if child.custom_id == "select":
                child.disabled = True
        try:
            await self.response.edit(view=self)
        except:
            pass

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user == self.author

    def build_embed(self, category: str) -> discord.Embed:
        category = category.lower()
        # Handle news/thông tin category
        if category == "news" or category == "thông tin":
            embed = discord.Embed(
                title="Thông báo nào đó...", 
                url="https://discord.com/channels/811542332678996008/811909963718459392/1069971173116481636", 
                color=func.settings.embed_color
            )
            
            categories_list = ["Tin tức", "Hướng dẫn"] + self.categories
            formatted_cats = []
            
            for i, cat in enumerate(categories_list, 1):
                prefix = "👉" if cat == "Tin tức" else str(i) + "."
                formatted_cats.append(f"{prefix} {cat}")
                
            embed.add_field(
                name=f"Các mục đang có: [{len(categories_list)}]",
                value="```py\n{}\n```".format("\n".join(formatted_cats)),
                inline=True
            )
            
            embed.add_field(
                name="📰 Thông tin:", 
                value="MiaSitas là bản fork của discord bot [Vocard](https://vocard.xyz)(bởi ChocoMeow) được Việt hóa cộng thêm những chỉnh sửa nhỏ bởi Aretzera.",
                inline=True
            )
            embed.add_field(
                name="Cách sử dụng cơ bản:", 
                value="```Vào 1 kênh voice nào đó rồi dùng /play {Tên nhạc/link của nó} để bật nhạc.```",
                inline=False
            )
            
            return embed
            
        # Handle tutorial and other categories
        embed = discord.Embed(
            title=f"Mục: {category.capitalize()}", 
            color=func.settings.embed_color
        )
        
        # Add categories list
        embed.add_field(
            name=f"Mục: [{2 + len(self.categories)}]",
            value="```py\n" + "\n".join(
                ("👉 " if c == category.capitalize() else f"{i}. ") + c
                for i, c in enumerate(['News', 'Tutorial'] + self.categories, start=1)
            ) + "```",
            inline=True
        )
        
        # Handle tutorial category
        if category == 'tutorial':
            embed.description = "Có thể xem qua video này để biết được các lệnh cơ bản(do owner Vocard thực hiện)."
            embed.set_image(url="https://cdn.discordapp.com/attachments/674788144931012638/917656288899514388/final_61aef3aa7836890135c6010c_669380.gif")
        # Handle other categories
        else:
            try:
                cog = next(c for _, c in self.bot.cogs.items() if _.lower() == category)
                commands = [cmd for cmd in cog.walk_commands()]
                embed.description = cog.description
                embed.add_field(
                    name=f"Các lệnh tại {category} : [{len(commands)}]",
                    value="```{}```".format(
                        "".join(f"/{cmd.qualified_name}\n" 
                        for cmd in commands 
                        if cmd.qualified_name != cog.qualified_name)
                    )
                )
            except StopIteration:
                embed.description = "Không tìm thấy lệnh nào trong mục này."
        
        return embed