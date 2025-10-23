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

import discord, copy
import function as func

from typing import List
from discord.ext import commands

class Modal(discord.ui.Modal):
    def __init__(self, items: List[discord.ui.Item], *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        for item in items:
            self.add_item(item)
        
        self.values: dict = {}
        
    async def on_submit(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer()
        for children in self.children:
            self.values[children.label.lower()] = children.value

        self.stop()

class Dropdown(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label='Hoạt động', description='Trạng thái của bot khi hoạt động', emoji='🟩'),
            discord.SelectOption(label='Không hoạt động', description='Trạng thái embed của bot khi không hoạt động', emoji='🟥'),
        ]
        super().__init__(placeholder='Select a embed to edit...', min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        self.view.embedType = self.values[0].lower()
        if self.view.embedType not in self.view.data:
            self.view.data[self.view.embedType] = {}

        await interaction.response.edit_message(embed=self.view.build_embed())

class EmbedBuilderView(discord.ui.View):
    def __init__(self, context: commands.Context, data: dict) -> None:
        from voicelink import Placeholders, build_embed

        super().__init__(timeout=300)
        self.add_item(Dropdown())

        self.author: discord.Member = context.author
        self.response: discord.Message = None

        self.original_data: dict = copy.deepcopy(data)
        self.data: dict = copy.deepcopy(data)
        self.embedType: str = "active"

        self.ph: Placeholders = Placeholders(context.bot)
        self.build_embed = lambda: build_embed(self.data.get(self.embedType, {}), self.ph)
    
    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        try:
            await self.response.edit(view=self)
        except:
            pass

    async def interaction_check(self, interaction: discord.Interaction):
        return interaction.user == self.author

    @discord.ui.button(label="Chỉnh sửa nội dung", style=discord.ButtonStyle.blurple)
    async def edit_content(self, interaction: discord.Interaction, button: discord.ui.Button):
        data = self.data.get(self.embedType, {})
        items = [
            discord.ui.TextInput(
                abel="Tiêu đề",
                placeholder="Tiêu đề gì gì đó",
                style=discord.TextStyle.paragraph,
                max_length=1000,
                default=data.get("title", {}).get("name"),
                required=False
            ),
            discord.ui.TextInput(
                label="Url",
                placeholder="Url của embed",
                style=discord.TextStyle.short,
                max_length=100,
                default=data.get("title", {}).get("url"),
                required=False
            ),
            discord.ui.TextInput(
                label="Màu",
                placeholder="Màu của tiêu đề",
                style=discord.TextStyle.short,
                max_length=100,
                default=data.get("color"),
                required=False
            ),
            discord.ui.TextInput(
                label="Mô tả",
                placeholder="Mô tả của tiêu đề",
                style=discord.TextStyle.paragraph,
                max_length=200,
                default=data.get("description"),
                required=False
            )
        ]

        modal = Modal(items, title="Chỉnh sửa nội dung")
        await interaction.response.send_modal(modal)
        await modal.wait()

        v = modal.values
        try:
            data["description"] = v["description"]
            data["color"] = int(v["color"], 16)

            if "title" not in data:
                data["title"] = {}

            data["title"]["name"] = v['title']
            data["title"]["url"] = v['url']
        except:
            pass

        return await interaction.edit_original_response(embed=self.build_embed())

    @discord.ui.button(label="Chỉnh sửa tên tác giả",)
    async def edit_author(self, interaction: discord.Interaction, button: discord.ui.Button):
        data = self.data.get(self.embedType, {})
        items = [
            discord.ui.TextInput(
                label="Tên",
                placeholder="Tên của tác giả",
                style=discord.TextStyle.paragraph,
                max_length=200,
                default=data.get("author", {}).get("name"),
                required=False
            ),
            discord.ui.TextInput(
                label="Url",
                placeholder="Url của tác giả",
                style=discord.TextStyle.short,
                max_length=100,
                default=data.get("author", {}).get("url"),
                required=False
            ),
            discord.ui.TextInput(
                label="Icon Url",
                placeholder="Url của icon tác giả",
                style=discord.TextStyle.short,
                max_length=100,
                default=data.get("author", {}).get("icon_url"),
                required=False
            ),
        ]

        modal = Modal(items, title="Chỉnh sửa tên tác giả")
        await interaction.response.send_modal(modal)
        await modal.wait()

        v = modal.values

        if v['name'] != "":
            if "author" not in data:
                data["author"] = {}
                
            data["author"]["name"] = v['name']
            data["author"]["url"] = v['url']
            data["author"]["icon_url"] = v['icon url']
        else:
            del data["author"]

        return await interaction.edit_original_response(embed=self.build_embed())
    
    @discord.ui.button(label="Chỉnh sửa ảnh")
    async def edit_image(self, interaction: discord.Interaction, button: discord.ui.Button):
        data = self.data.get(self.embedType, {})
        items = [
            discord.ui.TextInput(
                label="Ảnh đại diện",
                placeholder="Url của ảnh đại diện",
                style=discord.TextStyle.short,
                max_length=200,
                default=data.get("thumbnail"),
                required=False
            ),
            discord.ui.TextInput(
                label="Ảnh",
                placeholder="Url của ảnh",
                style=discord.TextStyle.short,
                max_length=100,
                default=data.get("image"),
                required=False
            )
        ]

        modal = Modal(items, title="Chỉnh sửa ảnh")
        await interaction.response.send_modal(modal)
        await modal.wait()

        v = modal.values

        data["thumbnail"] = v['thumbnail']
        data["image"] = v['image']

        return await interaction.edit_original_response(embed=self.build_embed())
    
    @discord.ui.button(label="Chỉnh sửa Footer")
    async def edit_footer(self, interaction: discord.Interaction, button: discord.ui.Button):
        data = self.data.get(self.embedType, {})
        items = [
            discord.ui.TextInput(
                label="Chữ",
                placeholder="Chữ của footer",
                style=discord.TextStyle.paragraph,
                max_length=200,
                default=data.get("footer", {}).get("text"),
                required=False
            ),
            discord.ui.TextInput(
                label="Url của Icon",
                placeholder="Url của icon footer",
                style=discord.TextStyle.short,
                max_length=100,
                default=data.get("footer", {}).get("icon_url"),
                required=False
            )
        ]

        modal = Modal(items, title="Chỉnh sủa Footer")
        await interaction.response.send_modal(modal)
        await modal.wait()

        v = modal.values
        if "footer" not in data:
            data["footer"] = {}

        data["footer"]["text"] = v['text']
        data["footer"]["icon_url"] = v['icon url']

        return await interaction.edit_original_response(embed=self.build_embed())
    
    @discord.ui.button(label="Thêm field", style=discord.ButtonStyle.green, row=1)
    async def add_field(self, interaction: discord.Interaction, button: discord.ui.Button):
        data = self.data.get(self.embedType)
        items = [
            discord.ui.TextInput(
                label="Tên",
                placeholder="Tên của field",
                style=discord.TextStyle.paragraph,
                max_length=256
            ),
            discord.ui.TextInput(
                label="Giá trị",
                placeholder="Giá trị của field",
                style=discord.TextStyle.long,
                max_length=1024
            ),
            discord.ui.TextInput(
                label="Inline",
                placeholder="Chỉnh inline của field, ví dụ True hoặc False",
                style=discord.TextStyle.short
            )
        ]

        if "fields" not in data:
            data["fields"] = []

        if len(data["fields"]) >= 25:
            return await interaction.response.send_message("Bạn đã đầy field và không thể thêm đươc nữa!", ephemeral=True)
        
        modal = Modal(items, title="Thêm field")
        await interaction.response.send_modal(modal)
        await modal.wait()

        v = modal.values
        data["fields"].append({
            "name": v["name"],
            "value": v["value"],
            "inline": True if v["inline"].lower() == "true" else False
        })

        return await interaction.edit_original_response(embed=self.build_embed())
    
    @discord.ui.button(label="Bỏ field", style=discord.ButtonStyle.red, row=1)
    async def remove_field(self, interaction: discord.Interaction, button: discord.ui.Button):
        items = [
            discord.ui.TextInput(
                label="Chỉ số",
                placeholder="Chỉ số của field bạn muốn bỏ, ví dụ 0, 1, 2...",
                style=discord.TextStyle.short
            )
        ]

        data = self.data.get(self.embedType)
        if "fields" not in data:
            data["fields"] = []

        if len(data["fields"]) == 0:
            return await interaction.response.send_message("Không có field để bỏ!", ephemeral=True)
        
        modal = Modal(items, title="Remove Field")
        await interaction.response.send_modal(modal)
        await modal.wait()

        try:
            del data["fields"][int(modal.values["index"])]
        except:
            return await interaction.followup.send("Không tìm thấy field!", ephemeral=True)
        
        return await interaction.edit_original_response(embed=self.build_embed())

    @discord.ui.button(label="Áp dụng", style=discord.ButtonStyle.green, row=1)
    async def apply(self, interaction: discord.Interaction, button: discord.ui.Button):
        await func.update_settings(
            interaction.guild_id,
            {"$set": {"default_controller.embeds": self.data}},
        )

        await self.on_timeout()
        await interaction.response.defer()
        self.stop()

    @discord.ui.button(label="Reset", style=discord.ButtonStyle.red, row=1)
    async def reset(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.data.update(copy.deepcopy(self.original_data))
        return await interaction.response.edit_message(embed=self.build_embed())

    @discord.ui.button(emoji='🗑️', row=1)
    async def stop_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.response.delete()
        self.stop()

        