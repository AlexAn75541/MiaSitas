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
import copy

from discord.ext import commands

from .utils import BaseModal
from ..mongodb import MongoDBHandler
from ..placeholders import PlayerPlaceholder


class Dropdown(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label='Đang hoạt động', value='active', description='Embed bộ điều khiển khi nhạc đang phát', emoji='🟩'),
            discord.SelectOption(label='Không hoạt động', value='inactive', description='Embed bộ điều khiển khi nhạc không phát', emoji='🟥'),
        ]
        super().__init__(placeholder='Chọn một embed để chỉnh sửa...', min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        self.view.embed_type = self.values[0].lower()
        if self.view.embed_type not in self.view.data:
            self.view.data[self.view.embed_type] = {}

        await interaction.response.edit_message(embed=self.view.build_embed())

class EmbedBuilderView(discord.ui.View):
    def __init__(self, context: commands.Context, placeholder: PlayerPlaceholder, data: dict) -> None:
        super().__init__(timeout=300)
        self.add_item(Dropdown())

        self.author: discord.Member = context.author
        self.ph: PlayerPlaceholder = placeholder
        self.response: discord.Message = None

        self.original_data: dict = copy.deepcopy(data)
        self.data: dict = copy.deepcopy(data)
        self.embed_type: str = "active"
    
    def build_embed(self) -> discord.Embed:
        return PlayerPlaceholder.build_embed(self.data.get(self.embed_type, {}), self.ph)
    
    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        try:
            await self.response.edit(view=self)
        except:
            pass

    async def interaction_check(self, interaction: discord.Interaction):
        return interaction.user == self.author

    @discord.ui.button(label="Chỉnh sửa Nội dung", style=discord.ButtonStyle.blurple)
    async def edit_content(self, interaction: discord.Interaction, button: discord.ui.Button):
        data = self.data.get(self.embed_type, {})
        modal = BaseModal(
            title="Chỉnh sửa Nội dung",
            custom_id="edit_content",
            items=[
                discord.ui.TextInput(
                    label="Tiêu đề",
                    placeholder="Tiêu đề của embed",
                    style=discord.TextStyle.paragraph,
                    custom_id="title",
                    max_length=1000,
                    default=data.get("title", {}).get("name"),
                    required=False
                ),
                discord.ui.TextInput(
                    label="Url",
                    placeholder="URL của tiêu đề",
                    style=discord.TextStyle.short,
                    custom_id="url",
                    max_length=100,
                    default=data.get("title", {}).get("url"),
                    required=False
                ),
                discord.ui.TextInput(
                    label="Màu",
                    placeholder="Màu của embed",
                    style=discord.TextStyle.short,
                    custom_id="color",
                    max_length=100,
                    default=data.get("color"),
                    required=False
                ),
                discord.ui.TextInput(
                    label="Mô tả",
                    placeholder="Mô tả của embed",
                    style=discord.TextStyle.paragraph,
                    custom_id="description",
                    max_length=200,
                    default=data.get("description"),
                    required=False
                )
        ])
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

        return await self.response.edit(embed=self.build_embed())

    @discord.ui.button(label="Chỉnh sửa Tác giả",)
    async def edit_author(self, interaction: discord.Interaction, button: discord.ui.Button):
        data = self.data.get(self.embed_type, {})
        modal = BaseModal(
            title="Chỉnh sửa Tác giả",
            custom_id="edit_author",
            items=[
                discord.ui.TextInput(
                    label="Tên",
                    placeholder="Tên của tác giả",
                    style=discord.TextStyle.paragraph,
                    custom_id="name",
                    max_length=200,
                    default=data.get("author", {}).get("name"),
                    required=False
                ),
                discord.ui.TextInput(
                    label="Url",
                    placeholder="URL của tác giả",
                    style=discord.TextStyle.short,
                    custom_id="url",
                    max_length=100,
                    default=data.get("author", {}).get("url"),
                    required=False
                ),
                discord.ui.TextInput(
                    label="URL Ảnh đại diện",
                    placeholder="URL ảnh đại diện của tác giả",
                    style=discord.TextStyle.short,
                    custom_id="icon_url",
                    max_length=100,
                    default=data.get("author", {}).get("icon_url"),
                    required=False
                ),
        ])
        await interaction.response.send_modal(modal)
        await modal.wait()

        v = modal.values
        if v['name'] != "":
            if "author" not in data:
                data["author"] = {}
                
            data["author"]["name"] = v['name']
            data["author"]["url"] = v['url']
            data["author"]["icon_url"] = v['icon_url']
        else:
            del data["author"]

        return await self.response.edit(embed=self.build_embed())
    
    @discord.ui.button(label="Chỉnh sửa Hình ảnh")
    async def edit_image(self, interaction: discord.Interaction, button: discord.ui.Button):
        data = self.data.get(self.embed_type, {})
        modal = BaseModal(
            title="Chỉnh sửa Hình ảnh",
            custom_id="edit_image",
            items=[
                discord.ui.TextInput(
                    label="Ảnh thu nhỏ",
                    placeholder="URL của ảnh thu nhỏ",
                    style=discord.TextStyle.short,
                    custom_id="thumbnail",
                    max_length=200,
                    default=data.get("thumbnail"),
                    required=False
                ),
                discord.ui.TextInput(
                    label="Hình ảnh",
                    placeholder="URL của hình ảnh",
                    style=discord.TextStyle.short,
                    custom_id="image",
                    max_length=100,
                    default=data.get("image"),
                    required=False
                )
        ])
        await interaction.response.send_modal(modal)
        await modal.wait()

        v = modal.values
        data["thumbnail"] = v['thumbnail']
        data["image"] = v['image']

        return await self.response.edit(embed=self.build_embed())
    
    @discord.ui.button(label="Chỉnh sửa Chân trang")
    async def edit_footer(self, interaction: discord.Interaction, button: discord.ui.Button):
        data = self.data.get(self.embed_type, {})
        modal = BaseModal(
            title="Chỉnh sửa Chân trang",
            custom_id="edit_footer",
            items=[
                discord.ui.TextInput(
                    label="Văn bản",
                    placeholder="Văn bản của chân trang",
                    style=discord.TextStyle.paragraph,
                    custom_id="text",
                    max_length=200,
                    default=data.get("footer", {}).get("text"),
                    required=False
                ),
                discord.ui.TextInput(
                    label="URL Biểu tượng",
                    placeholder="URL của biểu tượng",
                    style=discord.TextStyle.short,
                    custom_id="icon_url",
                    max_length=100,
                    default=data.get("footer", {}).get("icon_url"),
                    required=False
                )
        ])
        await interaction.response.send_modal(modal)
        await modal.wait()

        v = modal.values
        if "footer" not in data:
            data["footer"] = {}

        data["footer"]["text"] = v['text']
        data["footer"]["icon_url"] = v['icon_url']

        return await self.response.edit(embed=self.build_embed())
    
    @discord.ui.button(label="Thêm Trường", style=discord.ButtonStyle.green, row=1)
    async def add_field(self, interaction: discord.Interaction, button: discord.ui.Button):
        data = self.data.get(self.embed_type)
        if "fields" not in data:
            data["fields"] = []

        if len(data["fields"]) >= 25:
            return await interaction.response.send_message("Bạn đã đạt số lượng trường tối đa!", ephemeral=True)
        
        modal = BaseModal(
            title="Thêm Trường",
            custom_id="add_field",
            items=[
                discord.ui.TextInput(
                    label="Tên",
                    placeholder="Tên của trường",
                    style=discord.TextStyle.paragraph,
                    custom_id="name",
                    max_length=256
                ),
                discord.ui.TextInput(
                    label="Giá trị",
                    placeholder="Giá trị của trường",
                    style=discord.TextStyle.long,
                    custom_id="value",
                    max_length=1024
                ),
                discord.ui.TextInput(
                    label="Cùng dòng",
                    placeholder="Cùng dòng của trường, ví dụ True hoặc False",
                    style=discord.TextStyle.short,
                    custom_id="inline",
                )
        ])
        await interaction.response.send_modal(modal)
        await modal.wait()

        v = modal.values
        data["fields"].append({
            "name": v["name"],
            "value": v["value"],
            "inline": True if v["inline"].lower() == "true" else False
        })

        return await self.response.edit(embed=self.build_embed())
    
    @discord.ui.button(label="Xóa Trường", style=discord.ButtonStyle.red, row=1)
    async def remove_field(self, interaction: discord.Interaction, button: discord.ui.Button):
        data = self.data.get(self.embed_type)
        if "fields" not in data:
            data["fields"] = []

        if len(data["fields"]) == 0:
            return await interaction.response.send_message("Không có trường nào để xóa!", ephemeral=True)
        
        modal = BaseModal(
            title="Xóa Trường",
            custom_id="remove_field",
            items = [
                discord.ui.TextInput(
                    label="Số thứ tự",
                    placeholder="Số thứ tự của trường cần xóa, ví dụ 1",
                    style=discord.TextStyle.short,
                    custom_id="index",
                )
        ])
        await interaction.response.send_modal(modal)
        await modal.wait()

        try:
            del data["fields"][int(modal.values["index"])]
        except:
            return await interaction.followup.send("Không tìm thấy trường", ephemeral=True)
        
        return await self.response.edit(embed=self.build_embed())

    @discord.ui.button(label="Áp dụng", style=discord.ButtonStyle.green, row=1)
    async def apply(self, interaction: discord.Interaction, button: discord.ui.Button):
        await MongoDBHandler.update_settings(
            interaction.guild_id,
            {"$set": {"default_controller.embeds": self.data}},
        )

        await self.on_timeout()
        await interaction.response.defer()
        self.stop()

    @discord.ui.button(label="Đặt lại", style=discord.ButtonStyle.red, row=1)
    async def reset(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.data.update(copy.deepcopy(self.original_data))
        return await interaction.response.edit_message(embed=self.build_embed())

    @discord.ui.button(emoji='🗑️', row=1)
    async def stop_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.response.delete()
        self.stop()

        