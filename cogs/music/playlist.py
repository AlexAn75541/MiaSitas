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

import time
import discord
import voicelink

from io import StringIO
from typing import Optional, Tuple
from discord import app_commands
from discord.ext import commands
from function import (
    get_aliases,
    cooldown_check,
    logger
)

from voicelink import MongoDBHandler, Config
from voicelink.views import PlaylistViewManager, InboxView, HelpView
from voicelink.utils import format_ms, dispatch_message, send_localized_message

def assign_playlist_id(existed: list) -> str:
    for i in range(200, 210):
        if str(i) not in existed:
            return str(i)

def resolve_owner_display(ctx: commands.Context[commands.Bot], owner_id: int):
    if owner_id == ctx.author.id:
        return ctx.author
    if ctx.guild:
        member = ctx.guild.get_member(owner_id)
        if member:
            return member
    user = ctx.bot.get_user(owner_id)
    return user if user else f"<@{owner_id}>"

async def check_playlist_perms(
    user_id: int,
    author_id: int,
    playlist_id: str,
    *,
    required_perm: Optional[str] = "read"
) -> Tuple[Optional[dict], Optional[str]]:
    """Check if user has the requested permissions for a specific playlist."""
    user_data = await MongoDBHandler.get_user(author_id, d_type='playlist')
    playlist = user_data.get(playlist_id)
    
    if not playlist:
        return None, "not_found"
    
    perms = playlist.get('perms', {})
    if user_id not in perms.get('read', []):
        return None, "no_read"
    
    if required_perm and required_perm != "read":
        if user_id not in perms.get(required_perm, []):
            return None, "no_permission"
    
    return playlist, None

async def check_playlist(
    ctx: commands.Context,
    name: str = None,
    full: bool = False,
    share: bool = True,
    share_perm: Optional[str] = None
) -> dict:
    """Get user's playlist data with various filtering options."""
    user_playlists = await MongoDBHandler.get_user(ctx.author.id, d_type='playlist')

    if isinstance(ctx, discord.Interaction) and not ctx.interaction.response.is_done():
        await ctx.defer()
    
    if full:
        return user_playlists
    
    if not name:
        return {
            'playlist': user_playlists['200'],
            'position': 1,
            'id': "200",
            'is_shared': False,
            'owner_id': ctx.author.id,
            'owner_playlist_id': "200",
            'error': None
        }
    
    for index, playlist_id in enumerate(user_playlists, start=1):
        playlist = user_playlists[playlist_id]
        
        if playlist['name'].lower() == name.lower():
            if playlist['type'] == 'share' and share:
                shared_playlist, error = await check_playlist_perms(
                    ctx.author.id,
                    playlist['user'],
                    playlist['referId'],
                    required_perm=share_perm or "read"
                )
                
                if not shared_playlist:
                    if error == "not_found":
                        await MongoDBHandler.update_user(ctx.author.id, {"$unset": {f"playlist.{playlist_id}": 1}})
                    return {
                        'playlist': None,
                        'position': index,
                        'id': playlist_id,
                        'is_shared': True,
                        'owner_id': playlist['user'],
                        'owner_playlist_id': playlist['referId'],
                        'error': 'permission' if error in {'no_read', 'no_permission'} else None
                    }
                
                return {
                    'playlist': shared_playlist,
                    'position': index,
                    'id': playlist_id,
                    'is_shared': True,
                    'owner_id': playlist['user'],
                    'owner_playlist_id': playlist['referId'],
                    'error': None
                }
            
            return {
                'playlist': playlist,
                'position': index,
                'id': playlist_id,
                'is_shared': False,
                'owner_id': ctx.author.id,
                'owner_playlist_id': playlist_id,
                'error': None
            }
    
    return {
        'playlist': None,
        'position': None,
        'id': None,
        'is_shared': False,
        'owner_id': ctx.author.id,
        'owner_playlist_id': None,
        'error': None
    }

async def search_playlist(url: str, requester: discord.Member, time_needed: bool = True) -> dict:
    """Search for playlist tracks from a URL."""
    try:
        tracks = await voicelink.NodePool.get_node().get_tracks(url, requester=requester)
        result = {"name": tracks.name, "tracks": tracks.tracks}
        
        if time_needed:
            result["time"] = format_ms(sum(track.length for track in tracks.tracks))
        
        return result
    except Exception:
        return {}

async def _process_playlist(ctx: commands.Context, playlist_data: dict, playlist_id: str, is_locked: bool):
    """Process a single playlist and return its formatted data."""
    playlist_type = playlist_data['type']
    
    # Get appropriate emoji
    if is_locked:
        emoji = '🔒'
    elif playlist_type == 'link':
        emoji = '🌐'
    elif playlist_type == 'share':
        emoji = '🤝'
    else:
        emoji = '❤️'
    
    # Handle link playlist
    if playlist_type == 'link':
        tracks = await search_playlist(playlist_data['uri'], requester=ctx.author)
        if not tracks:
            return None
        
        return {
            'emoji': emoji,
            'id': playlist_id,
            'time': tracks['time'],
            'name': playlist_data['name'],
            'tracks': tracks['tracks'],
            'perms': playlist_data['perms'],
            'type': playlist_data['type']
        }
    
    # Handle shared playlist
    if playlist_type == 'share':
        shared_playlist, error = await check_playlist_perms(
            ctx.author.id, 
            playlist_data['user'], 
            playlist_data['referId']
        )
        
        if not shared_playlist:
            if error == "not_found":
                await MongoDBHandler.update_user(ctx.author.id, {"$unset": {f"playlist.{playlist_id}": 1}})
            return None
        
        if shared_playlist['type'] == 'link':
            tracks = await search_playlist(shared_playlist['uri'], requester=ctx.author)
            if not tracks:
                return None
            
            return {
                'emoji': emoji,
                'id': playlist_id,
                'time': tracks['time'],
                'name': playlist_data['name'],
                'tracks': tracks['tracks'],
                'perms': shared_playlist['perms'],
                'owner': playlist_data['user'],
                'type': 'share'
            }
        
        decoded_tracks = []
        total_time = 0
        for track in shared_playlist['tracks']:
            decoded_track = voicelink.Track.decode(track)
            total_time += decoded_track.get("length", 0)
            decoded_tracks.append(decoded_track)
        
        return {
            'emoji': emoji,
            'id': playlist_id,
            'time': format_ms(total_time),
            'name': playlist_data['name'],
            'tracks': decoded_tracks,
            'perms': shared_playlist['perms'],
            'owner': playlist_data['user'],
            'type': 'share'
        }
    
    decoded_tracks = []
    total_time = 0
    for track in playlist_data['tracks']:
        decoded_track = voicelink.Track.decode(track)
        total_time += decoded_track.get("length", 0)
        decoded_tracks.append(decoded_track)
    
    return {
        'emoji': emoji,
        'id': playlist_id,
        'time': format_ms(total_time),
        'name': playlist_data['name'],
        'tracks': decoded_tracks,
        'perms': playlist_data['perms'],
        'owner': playlist_data.get('owner', ctx.author.id),
        'type': playlist_data['type']
    }

class Playlists(commands.Cog, name="playlist"):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.description = "Đây là hệ thống playlist của MiaSitas. Bạn có thể lưu các bài hát yêu thích và dùng MiaSitas để phát trên bất kỳ máy chủ nào."

    async def playlist_autocomplete(self, interaction: discord.Interaction, current: str) -> list:
        playlists_raw: dict[str, dict] = await MongoDBHandler.get_user(interaction.user.id, d_type='playlist')
        playlists = [value['name'] for value in playlists_raw.values()] if playlists_raw else []
        if current:
            return [app_commands.Choice(name=p, value=p) for p in playlists if current in p]
        return [app_commands.Choice(name=p, value=p) for p in playlists]

    @commands.hybrid_group(
        name="playlist", 
        aliases=get_aliases("playlist"),
        invoke_without_command=True
    )
    async def playlist(self, ctx: commands.Context):
        view = HelpView(self.bot, ctx.author)
        embed = view.build_embed(self.qualified_name)
        view.response = dispatch_message(ctx, embed, view=view)

    @playlist.command(name="play", aliases=get_aliases("play"))
    @app_commands.describe(
        name="Nhập tên playlist của bạn",
        value="Phát bài hát cụ thể từ playlist của bạn."
    )
    @app_commands.autocomplete(name=playlist_autocomplete)
    @commands.dynamic_cooldown(cooldown_check, commands.BucketType.guild)
    async def play(self, ctx: commands.Context, name: str = None, value: int = None) -> None:
        "Phát tất cả bài hát từ playlist yêu thích của bạn."
        result = await check_playlist(ctx, name.lower() if name else None)

        if not result['playlist']:
            return await send_localized_message(ctx, 'playlist.errors.notFound', name, ephemeral=True)
        max_p, max_t, _ = Config().get_playlist_config()
        if result['position'] > max_p:
            return await send_localized_message(ctx, 'playlist.errors.noAccess', ephemeral=True)

        player: voicelink.Player = ctx.guild.voice_client
        if not player:
            player = await voicelink.connect_channel(ctx)

        if result['playlist']['type'] == 'link':
            tracks = await search_playlist(result['playlist']['uri'], ctx.author, time_needed=False)
        else:
            if not result['playlist']['tracks']:
                return await send_localized_message(ctx, 'playlist.errors.noTrack', result['playlist']['name'], ephemeral=True)

            _tracks = []
            for track in result['playlist']['tracks'][:max_t]:
                _tracks.append(voicelink.Track(track_id=track, info=voicelink.Track.decode(track), requester=ctx.author))
                    
            tracks = {"name": result['playlist']['name'], "tracks": _tracks}

        if not tracks:
            return await send_localized_message(ctx, 'playlist.errors.noTrack', result['playlist']['name'], ephemeral=True)

        if value and 0 < value <= (len(tracks['tracks'])):
            tracks['tracks'] = [tracks['tracks'][value - 1]]
        await player.add_track(tracks['tracks'])
        await send_localized_message(ctx, 'playlist.actions.play', result['playlist']['name'], len(tracks['tracks'][:max_t]))

        if not player.is_playing:
            await player.do_next()

    @playlist.command(name="view", aliases=get_aliases("view"))
    @commands.dynamic_cooldown(cooldown_check, commands.BucketType.guild)
    async def view(self, ctx: commands.Context) -> None:
        """Liệt kê tất cả playlist của bạn và các bài hát trong playlist yêu thích."""
        user_playlists = await check_playlist(ctx, full=True)
        max_p, _, _ = Config().get_playlist_config()
        
        playlist_results = []
        
        for index, playlist_id in enumerate(user_playlists, start=1):
            playlist_data = user_playlists[playlist_id]
            is_locked = max_p < index
            
            try:
                result = await _process_playlist(ctx, playlist_data, playlist_id, is_locked)
                if result:
                    playlist_results.append(result)
            except Exception:
                playlist_results.append({
                    'emoji': '⛔',
                    'id': playlist_id,
                    'time': '--:--',
                    'name': 'Error',
                    'tracks': [],
                    'type': 'error'
                })
                
        view = PlaylistViewManager(ctx, playlist_results)
        view.response = await dispatch_message(ctx, content=view.build_embed(), view=view, ephemeral=True)

    @playlist.command(name="create", aliases=get_aliases("create"))
    @app_commands.describe(
        name="Đặt tên cho playlist của bạn.",
        link="Cung cấp liên kết playlist nếu bạn tạo playlist dạng liên kết."
    )
    @commands.dynamic_cooldown(cooldown_check, commands.BucketType.guild)
    async def create(self, ctx: commands.Context, name: str, link: str = None):
        "Tạo playlist tùy chỉnh của bạn."
        if len(name) > 10:
            return await send_localized_message(ctx, 'playlist.errors.nameOverLimit', ephemeral=True)
        
        max_p, _, _ = Config().get_playlist_config()
        user = await check_playlist(ctx, full=True)

        if len(user) >= max_p:
            return await send_localized_message(ctx, 'playlist.errors.limitReached', max_p, ephemeral=True)
        
        for data in user:
            if user[data]['name'].lower() == name.lower():
                return await send_localized_message(ctx, 'playlist.errors.exists', name, ephemeral=True)
        if link:
            tracks = await voicelink.NodePool.get_node().get_tracks(link, requester=ctx.author)
            if not isinstance(tracks, voicelink.Playlist):
                return await send_localized_message(ctx, "playlist.errors.invalidUrl", ephemeral=True)

        data = {'uri': link, 'perms': {'read': []}, 'name': name, 'type': 'link'} if link else {'tracks': [], 'perms': {'read': [], 'write': [], 'remove': []}, 'name': name, 'type': 'playlist'}
        await MongoDBHandler.update_user(ctx.author.id, {"$set": {f"playlist.{assign_playlist_id([data for data in user])}": data}})
        await send_localized_message(ctx, "playlist.actions.created", name)

    @playlist.command(name="delete", aliases=get_aliases("delete"))
    @app_commands.describe(name="Tên của playlist.")
    @app_commands.autocomplete(name=playlist_autocomplete)
    @commands.dynamic_cooldown(cooldown_check, commands.BucketType.guild)
    async def delete(self, ctx: commands.Context, name: str):
        "Xóa playlist tùy chỉnh của bạn."
        result = await check_playlist(ctx, name.lower(), share=False)
        if not result['playlist']:
            return await send_localized_message(ctx, "playlist.errors.notFound", name, ephemeral=True)
        if result['id'] == "200":
            return await send_localized_message(ctx, "playlist.errors.deleteDefault", ephemeral=True)

        if result['playlist']['type'] == 'share':
            await MongoDBHandler.update_user(result['playlist']['user'], {"$pull": {f"playlist.{result['playlist']['referId']}.perms.read": ctx.author.id}})

        await MongoDBHandler.update_user(ctx.author.id, {"$unset": {f"playlist.{result['id']}": 1}})
        return await send_localized_message(ctx, "playlist.actions.removed", result["playlist"]["name"])

    @playlist.command(name="share", aliases=get_aliases("share"))
    @app_commands.describe(
        member="ID người dùng của bạn bè.",
        name="Tên playlist bạn muốn chia sẻ."
    )
    @app_commands.autocomplete(name=playlist_autocomplete)
    @commands.dynamic_cooldown(cooldown_check, commands.BucketType.guild)
    async def share(self, ctx: commands.Context, member: discord.Member, name: str):
        "Chia sẻ playlist với bạn bè."
        if member.id == ctx.author.id:
            return await send_localized_message(ctx, 'playlist.sharing.sendErrorPlayer', ephemeral=True)
        if member.bot:
            return await send_localized_message(ctx, 'playlist.sharing.sendErrorBot', ephemeral=True)
        result = await check_playlist(ctx, name.lower(), share=False)
        if not result['playlist']:
            return await send_localized_message(ctx, 'playlist.errors.notFound', name, ephemeral=True)

        if result['playlist']['type'] == 'share':
            return await send_localized_message(ctx, 'playlist.sharing.belongs', result['playlist']['user'], ephemeral=True)
        if member.id in result['playlist']['perms']['read']:
            return await send_localized_message(ctx, 'playlist.sharing.alreadyShared', member, ephemeral=True)

        receiver = await MongoDBHandler.get_user(member.id)
        if not receiver:
            return await send_localized_message(ctx, 'playlist.sharing.noAccount', member)
        for mail in receiver['inbox']:
            if mail['sender'] == ctx.author.id and mail['referId'] == result['id']:
                return await send_localized_message(ctx, 'playlist.sharing.alreadySent', ephemeral=True)
        if len(receiver['inbox']) >= 10:
            return await send_localized_message(ctx, 'playlist.inbox.full', member, ephemeral=True)

        await MongoDBHandler.update_user(
            member.id, 
            {"$push": {"inbox": {
                'sender': ctx.author.id, 
                'referId': result['id'],
                'time': time.time(),
                'title': f'Lời mời playlist từ {ctx.author}',
                'description': f"Bạn được mời sử dụng playlist này.\nTên Playlist: {result['playlist']['name']}\nLoại Playlist: {result['playlist']['type']}",
                'type': 'invite'
            }}}
        )
        return await send_localized_message(ctx, "playlist.sharing.invitationSent", member)

    @playlist.command(name="permission", aliases=get_aliases("permission"))
    @app_commands.describe(
        name="Tên của playlist.",
        member="Người dùng cần cấp hoặc thu hồi quyền.",
        permission="Loại quyền: read, write, hoặc remove.",
        action="Cấp hoặc thu hồi quyền."
    )
    @app_commands.choices(permission=[
        app_commands.Choice(name="read", value="read"),
        app_commands.Choice(name="write", value="write"),
        app_commands.Choice(name="remove", value="remove")
    ])
    @app_commands.choices(action=[
        app_commands.Choice(name="grant", value="grant"),
        app_commands.Choice(name="revoke", value="revoke")
    ])
    @app_commands.autocomplete(name=playlist_autocomplete)
    @commands.dynamic_cooldown(cooldown_check, commands.BucketType.guild)
    async def permission(self, ctx: commands.Context, member: discord.Member, name: str, permission: str, action: str):
        "Cấp hoặc thu hồi quyền cho playlist."
        if member.id == ctx.author.id:
            return await send_localized_message(ctx, 'playlist.permissions.cannotModifySelf', ephemeral=True)
        if member.bot:
            return await send_localized_message(ctx, 'playlist.sharing.sendErrorBot', ephemeral=True)
        
        result = await check_playlist(ctx, name.lower(), share=False)
        if not result['playlist']:
            return await send_localized_message(ctx, 'playlist.errors.notFound', name, ephemeral=True)
        
        if result['playlist']['type'] in ['share', 'link']:
            return await send_localized_message(ctx, 'playlist.errors.notAllowed', ephemeral=True)
        
        perm_type = result['playlist'].get('perms', {})
        if permission not in perm_type:
            return await send_localized_message(ctx, 'playlist.permissions.invalidPermission', ephemeral=True)
        
        perm_list = perm_type.get(permission, [])
        if action == "grant":
            if member.id in perm_list:
                return await send_localized_message(ctx, 'playlist.permissions.alreadyGranted', member, permission, ephemeral=True)
            
            # Ensure user has read access first
            if permission != 'read' and member.id not in perm_type.get('read', []):
                return await send_localized_message(ctx, f'Bạn chưa chia sẻ playlist với {member.mention}', member, ephemeral=True)
            
            await MongoDBHandler.update_user(ctx.author.id, {"$push": {f"playlist.{result['id']}.perms.{permission}": member.id}})
            return await send_localized_message(ctx, 'playlist.permissions.granted', member, permission, result['playlist']['name'])
        
        elif action == "revoke":
            if member.id not in perm_list:
                return await send_localized_message(ctx, 'playlist.permissions.notGranted', member, permission, ephemeral=True)
            
            await MongoDBHandler.update_user(ctx.author.id, {"$pull": {f"playlist.{result['id']}.perms.{permission}": member.id}})
            
            # If revoking read, also revoke write and remove
            if permission == 'read':
                await MongoDBHandler.update_user(ctx.author.id, {"$pull": {f"playlist.{result['id']}.perms.write": member.id}})
                await MongoDBHandler.update_user(ctx.author.id, {"$pull": {f"playlist.{result['id']}.perms.remove": member.id}})
            
            return await send_localized_message(ctx, 'playlist.permissions.revoked', member, permission, result['playlist']['name'])
        
        else:
            return await send_localized_message(ctx, 'playlist.permissions.invalidAction', ephemeral=True)

    @playlist.command(name="rename", aliases=get_aliases("rename"))
    @app_commands.describe(
        name="Tên playlist của bạn.",
        newname="Tên mới của playlist."
    )
    @app_commands.autocomplete(name=playlist_autocomplete)
    @commands.dynamic_cooldown(cooldown_check, commands.BucketType.guild)
    async def rename(self, ctx: commands.Context, name: str, newname: str) -> None:
        "Đổi tên playlist tùy chỉnh của bạn."
        if len(newname) > 10:
            return await send_localized_message(ctx, 'playlist.errors.nameOverLimit', ephemeral=True)
        if name.lower() == newname.lower():
            return await send_localized_message(ctx, 'playlist.errors.sameName', ephemeral=True)
        user = await check_playlist(ctx, full=True)
        found, id = False, 0
        for data in user:
            if user[data]['name'].lower() == name.lower():
                found, id = True, data
            if user[data]['name'].lower() == newname.lower():
                return await send_localized_message(ctx, 'playlist.errors.exists', ephemeral=True)

        if not found:
            return await send_localized_message(ctx, 'playlist.errors.notFound', name, ephemeral=True)

        await MongoDBHandler.update_user(ctx.author.id, {"$set": {f'playlist.{id}.name': newname}})
        await send_localized_message(ctx, 'playlist.actions.renamed', name, newname)

    @playlist.command(name="inbox", aliases=get_aliases("inbox"))
    @commands.dynamic_cooldown(cooldown_check, commands.BucketType.guild)
    async def inbox(self, ctx: commands.Context) -> None:
        "Xem lời mời playlist của bạn."
        user = await MongoDBHandler.get_user(ctx.author.id)
        max_p, _, _ = Config().get_playlist_config()

        if not user['inbox']:
            return await send_localized_message(ctx, "playlist.inbox.noMessages", ephemeral=True)

        inbox = user['inbox'].copy()
        view = InboxView(ctx.author, user['inbox'])
        view.response = await dispatch_message(ctx, view.build_embed(), view=view, ephemeral=True)
        await view.wait()

        if inbox == user['inbox']:
            return
        
        update_data, dId = {}, {dId for dId in user["playlist"]}
        for data in view.new_playlist[:(max_p - len(user['playlist']))]:
            addId = assign_playlist_id(dId)
            await MongoDBHandler.update_user(data['sender'], {"$push": {f"playlist.{data['referId']}.perms.read": ctx.author.id}})
            update_data[f'playlist.{addId}'] = {
                'user': data['sender'], 'referId': data['referId'],
                'name': f"Share{time.strftime('%M%S', time.gmtime(int(data['time'])))}",
                'type': 'share'
            }
            update_data["inbox"] = view.inbox
            dId.add(addId)

        if update_data:
            await MongoDBHandler.update_user(ctx.author.id, {"$set": update_data})

    @playlist.command(name="add", aliases=get_aliases("add"))
    @commands.dynamic_cooldown(cooldown_check, commands.BucketType.guild)
    @app_commands.describe(
        name="Tên của playlist.",
        query="Nhập truy vấn hoặc liên kết có thể tìm kiếm."
    )
    @app_commands.autocomplete(name=playlist_autocomplete)
    async def add(self, ctx: commands.Context, name: str, query: str) -> None:
        "Thêm bài hát vào playlist tùy chỉnh của bạn."
        result = await check_playlist(ctx, name.lower(), share=True, share_perm='write')
        if not result['playlist']:
            if result.get('error') == 'permission':
                return await send_localized_message(ctx, 'playlist.errors.noAccess', ephemeral=True)
            return await send_localized_message(ctx, 'playlist.errors.notFound', name, ephemeral=True)
        if result['playlist']['type'] == 'link':
            return await send_localized_message(ctx, 'playlist.errors.notAllowed', ephemeral=True)
        
        _, max_t, _ = Config().get_playlist_config()
        if len(result['playlist']['tracks']) >= max_t:
            return await send_localized_message(ctx, 'playlist.errors.trackLimitReached', max_t, ephemeral=True)

        results = await voicelink.NodePool.get_node().get_tracks(query, requester=ctx.author)
        if not results:
            return await send_localized_message(ctx, 'player.errors.noTrackFound')
        
        if isinstance(results, voicelink.Playlist):
            return await send_localized_message(ctx, 'playlist.errors.playlistLinkNotAllowed', ephemeral=True)
        
        if results[0].is_stream:
            return await send_localized_message(ctx, 'playlist.errors.streamNotAllowed', ephemeral=True)

        owner_id = result.get('owner_id', ctx.author.id)
        owner_playlist_id = result.get('owner_playlist_id', result['id'])
        await MongoDBHandler.update_user(owner_id, {"$push": {f'playlist.{owner_playlist_id}.tracks': results[0].track_id}})
        owner_display = resolve_owner_display(ctx, owner_id)
        await send_localized_message(ctx, 'playlist.actions.trackAdded', results[0].title, owner_display, result['playlist']['name'])

    @playlist.command(name="remove", aliases=get_aliases("remove"))
    @commands.dynamic_cooldown(cooldown_check, commands.BucketType.guild)
    @app_commands.describe(
        name="Tên của playlist.",
        position="Nhập vị trí bài hát cần xóa từ playlist."
    )
    @app_commands.autocomplete(name=playlist_autocomplete)
    async def remove(self, ctx: commands.Context, name: str, position: int):
        "Xóa bài hát khỏi playlist yêu thích của bạn."
        result = await check_playlist(ctx, name.lower(), share=True, share_perm='remove')
        if not result['playlist']:
            if result.get('error') == 'permission':
                return await send_localized_message(ctx, 'playlist.errors.noAccess', ephemeral=True)
            return await send_localized_message(ctx, 'playlist.errors.notFound', name, ephemeral=True)
        if result['playlist']['type'] == 'link':
            return await send_localized_message(ctx, 'playlist.errors.notAllowed', ephemeral=True)
        if not 0 < position <= len(result['playlist']['tracks']):
            return await send_localized_message(ctx, 'playlist.errors.positionNotFound', position, name)

        owner_id = result.get('owner_id', ctx.author.id)
        owner_playlist_id = result.get('owner_playlist_id', result['id'])
        await MongoDBHandler.update_user(owner_id, {"$pull": {f'playlist.{owner_playlist_id}.tracks': result['playlist']['tracks'][position - 1]}})
        
        track = voicelink.Track.decode(result['playlist']['tracks'][position - 1])
        owner_display = resolve_owner_display(ctx, owner_id)
        await send_localized_message(ctx, 'playlist.actions.trackRemoved', track.get("title"), owner_display, name)

    @playlist.command(name="clear", aliases=get_aliases("clear"))
    @commands.dynamic_cooldown(cooldown_check, commands.BucketType.guild)
    @app_commands.autocomplete(name=playlist_autocomplete)
    async def clear(self, ctx: commands.Context, name: str) -> None:
        "Xóa tất cả bài hát khỏi playlist yêu thích của bạn."
        result = await check_playlist(ctx, name.lower(), share=True, share_perm='remove')
        if not result['playlist']:
            if result.get('error') == 'permission':
                return await send_localized_message(ctx, 'playlist.errors.noAccess', ephemeral=True)
            return await send_localized_message(ctx, 'playlist.errors.notFound', name, ephemeral=True)

        if result['playlist']['type'] == 'link':
            return await send_localized_message(ctx, 'playlist.errors.notAllowed', ephemeral=True)

        owner_id = result.get('owner_id', ctx.author.id)
        owner_playlist_id = result.get('owner_playlist_id', result['id'])
        await MongoDBHandler.update_user(owner_id, {"$set": {f'playlist.{owner_playlist_id}.tracks': []}})
        await send_localized_message(ctx, 'playlist.actions.cleared', name)

    @playlist.command(name="export", aliases=get_aliases("export"))
    @commands.dynamic_cooldown(cooldown_check, commands.BucketType.guild)
    @app_commands.autocomplete(name=playlist_autocomplete)
    async def export(self, ctx: commands.Context, name: str) -> None:
        "Xuất toàn bộ playlist ra tệp văn bản"
        result = await check_playlist(ctx, name.lower())
        if not result['playlist']:
            return await send_localized_message(ctx, 'playlist.errors.notFound', name, ephemeral=True)
        
        if result['playlist']['type'] == 'link':
            tracks = await search_playlist(result['playlist']['uri'], ctx.author, time_needed=False)
        else:
            if not result['playlist']['tracks']:
                return await send_localized_message(ctx, 'playlist.errors.noTrack', result['playlist']['name'], ephemeral=True)

            _tracks = []
            for track in result['playlist']['tracks']:
                _tracks.append(voicelink.Track(track_id=track, info=voicelink.Track.decode(track), requester=ctx.author))
                    
            tracks = {"name": result['playlist']['name'], "tracks": _tracks}

        if not tracks:
            return await send_localized_message(ctx, 'playlist.errors.noTrack', result['playlist']['name'], ephemeral=True)

        temp = ""
        raw = "----------->Raw Info<-----------\n"

        total_length = 0
        for index, track in enumerate(tracks['tracks'], start=1):
            temp += f"{index}. {track.title} [{format_ms(track.length)}]\n"
            raw += track.track_id
            if index != len(tracks['tracks']):
                raw += ","
            total_length += track.length

        temp = "!Nhớ đừng thay đổi tệp này!\n------------->Thông tin<-------------\nPlaylist: {} ({})\nNgười yêu cầu: {} ({})\nBài hát: {} - {}\n------------>Danh sách<------------\n".format(
            tracks['name'], result['playlist']['type'],
            ctx.author.display_name, ctx.author.id,
            len(tracks['tracks']), format_ms(total_length)
        ) + temp
        temp += raw

        await ctx.send(content="", file=discord.File(StringIO(temp), filename=f"{tracks['name']}_playlist.txt"))

    @playlist.command(name="import", aliases=get_aliases("import"))
    @app_commands.describe(name="Đặt tên cho playlist của bạn.")
    @commands.dynamic_cooldown(cooldown_check, commands.BucketType.guild)
    async def _import(self, ctx: commands.Context, name: str, attachment: discord.Attachment):
        "Tạo playlist tùy chỉnh của bạn."
        if len(name) > 10:
            return await send_localized_message(ctx, 'playlist.errors.nameOverLimit', ephemeral=True)
        
        max_p, _, _ = Config().get_playlist_config()
        user = await check_playlist(ctx, full=True)

        if len(user) >= max_p:
            return await send_localized_message(ctx, 'playlist.errors.limitReached', max_p, ephemeral=True)
        
        for data in user:
            if user[data]['name'].lower() == name.lower():
                return await send_localized_message(ctx, 'playlist.errors.exists', name, ephemeral=True)

        try:
            bytes = await attachment.read()
            track_ids = bytes.split(b"\n")[-1]
            track_ids = track_ids.decode().split(",")

            data = {'tracks': track_ids, 'perms': {'read': [], 'write': [], 'remove': []}, 'name': name, 'type': 'playlist'}
            await MongoDBHandler.update_user(ctx.author.id, {"$set": {f"playlist.{assign_playlist_id([data for data in user])}": data}})
            await send_localized_message(ctx, 'playlist.actions.create', name)

        except Exception as e:
            logger.error("Decode Error", exc_info=e)
            raise e

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Playlists(bot))