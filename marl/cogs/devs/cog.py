
from collections import deque
from typing import Union, Optional

import disnake
from disnake.ext import commands
from jishaku.paginators import (PaginatorEmbedInterface, PaginatorInterface,
                                WrappedPaginator)

from .utils import SITE_REQUESTS_TEMPLATE, URL_REGEX


class DeveloperSupportCog(commands.Cog):
    
    def __init__(self, bot: 'commands.Bot'):
        self.bot = bot

        self.ignorables = deque(maxlen=50)

    @commands.group('siterequest', aliases=['sr', 'siterequests', 'srequests'], invoke_without_command=True)
    @commands.guild_only()
    async def site_request(self, ctx: 'commands.Context'):

        site_requests = ctx.bot.database.get_guild_site_requests(ctx.guild.id)
        channels = site_requests.setdefault('channels', [])

        if not channels:
            return await self.send_smartly(ctx, "No site request channels are configured for this server.", color=disnake.Colour.brand_red())

        out = SITE_REQUESTS_TEMPLATE.format(
            "\n".join(f"- <#{_}>" for _ in channels),
            len(site_requests.setdefault('requests', [])),
            len(site_requests.setdefault('blacklisted', [])),
        )
        
        return await self.send_smartly(ctx, out)

    @site_request.command('channel', aliases=['chan', 'ch'])
    @commands.has_permissions(manage_guild=True)
    async def site_request_channel(self, ctx: 'commands.Context', *channels: 'disnake.TextChannel'):
        
        site_requests = ctx.bot.database.get_guild_site_requests(ctx.guild.id)
        channel_list = site_requests.setdefault('channels', [])

        unique = list(((set(_.id for _ in channels) or set((ctx.channel.id,))) - set(channel_list)))[:10 - len(channel_list)]

        if not unique:
            return await self.send_smartly("Failed; cannot have more than 10 channel listeners.", color=disnake.Colour.brand_red())

        channel_list.extend(unique)
        return await self.send_smartly(ctx, "Listening on {}".format(', '.join(f"<#{_}>" for _ in unique)), color=disnake.Colour.brand_green())

    @site_request.command('removechannel', aliases=['rmchan', 'rmchannel', 'rmch'])
    @commands.has_permissions(manage_guild=True)
    async def site_request_remove_channel(self, ctx: 'commands.Context', *channels: 'disnake.TextChannel'):
        
        site_requests = ctx.bot.database.get_guild_site_requests(ctx.guild.id)
        channel_list = site_requests.setdefault('channels', [])

        removable = set(channel_list).union((*(_.id for _ in channels),) or (ctx.channel.id,))

        if not removable:
            return await self.send_smartly("Failed; none of those channels were registered for listening.", color=disnake.Colour.brand_red())
        
        for _ in removable:
            channel_list.remove(_)

        return await self.send_smartly(ctx, "Removed from listening on {}".format(', '.join(f"<#{_}>" for _ in removable)), color=disnake.Colour.brand_green())


    @site_request.command(aliases=['v', 'show'])
    async def view(self, ctx: 'commands.Context'):
        return await self.send_viewer(ctx, self.iter_requests(ctx), "Viewing caught requests:")

    @site_request.command()
    async def announce(self, ctx: 'commands.Context'):
        
        site_requests = ctx.bot.database.get_guild_site_requests(ctx.guild.id)
        announce_state = site_requests.setdefault('announcements', False)

        new_state = not announce_state
        site_requests.update(announcements=new_state)

        return await self.send_smartly(ctx, "Set announcement state to: `{}`".format(new_state), color=disnake.Colour.brand_green())


    @site_request.command(aliases=['rm'])
    async def remove(self, ctx: 'commands.Context', url_or_index: 'Union[int, str]'):
        return await self.remove_requests(ctx, self.get_mutable_requests(ctx), url_or_index)

    @site_request.command(aliases=['append'])
    async def add(self, ctx: 'commands.Context', *, hosts: 'str'):
        return await self.site_requests_listener(ctx.message, hosts=hosts)

    @commands.Cog.listener('on_message')
    async def site_requests_listener(self, message: 'disnake.Message', *, hosts=None):

        content = hosts or message.content
        site_requests = self.bot.database.get_guild_site_requests(message.guild.id)

        if (hosts is None and message.channel.id not in site_requests.setdefault('channels', [])) or (hosts is None and message.id in self.ignorables):
            return
        
        announce = site_requests.setdefault('announcements', False)
        
        matches = set((_.group(0) for _ in URL_REGEX.finditer(content)))
        unfiltered = (matches - set((_.get('requested') for _ in site_requests.setdefault('requests', []))))
        requested = unfiltered - set((_.get('requested') for _ in site_requests.setdefault('blacklisted', [])))
    
        if not requested:
            if hosts is not None:
                return await message.add_reaction('❌')
            
            if matches:
                return await self.send_smartly(await self.bot.get_context(message), "Previously requested or blacklisted.", color=disnake.Colour.brand_red())

            return

        mutable = site_requests.setdefault('requests', [])

        for host in requested:
            mutable.append(
                {
                    'user': str(message.author),
                    'user_id': message.author.id,
                    'requested': host,
                    'message_url': message.jump_url,
                }
            )

        if not announce:
            return await message.add_reaction('✅')

        return await self.send_smartly(await self.bot.get_context(message), "Successfully added **{}** host(s) to requests.".format(len(requested)), color=disnake.Colour.brand_green())


    @site_request.group(aliases=['deny'], invoke_without_command=True)
    async def blacklist(self, ctx: 'commands.Context'):
        return await self.send_viewer(ctx, self.iter_requests(ctx, type_of="blacklisted"), "Viewing blacklisted requests:")

    @blacklist.command(name="add", aliases=['append'])
    @commands.has_permissions(manage_guild=True)
    async def bl_add(self, ctx: 'commands.Context', *, blacklisted_hosts: 'str'):
        hosts = set((_.group(0) for _ in URL_REGEX.finditer(blacklisted_hosts)))        
        new_hosts = hosts - set((_.get('requested') for _ in self.iter_requests(ctx, type_of='blacklisted')))

        if not new_hosts:
            return await self.send_smartly(ctx, "Failed; already in the blacklist.", color=disnake.Colour.brand_red())

        removed = []
        requests = self.get_mutable_requests(ctx)

        for requested_hosts in requests:
            if any(_.endswith(requested_hosts.get('requested')) for _ in new_hosts):
                requests.remove(requested_hosts)
                removed.append(requested_hosts)

        for host in new_hosts:
            self.append_request(ctx.bot.database, ctx.guild.id, str(ctx.author), ctx.author.id, ctx.message.jump_url, host, type_of='blacklisted')

        message = "Successfully added **{}**/{} unique blacklists.".format(len(new_hosts), len(hosts))

        if removed:
            message += "\n\nRemoved **{}** hosts for the new blacklist violation: \n{}".format(len(removed), "\n".join("{0}. [{1[user]}]({1[message_url]}): {1[requested]}".format(count, request) for count, request in enumerate(removed, 1)))

        return await self.send_smartly(ctx, message, color=disnake.Colour.brand_green())


    @blacklist.command(name='remove', aliases=['rm'])
    @commands.has_permissions(manage_guild=True)
    async def bl_remove(self, ctx: 'commands.Context', url_or_index: 'Union[int, str]'):
        return await self.remove_requests(ctx, self.get_mutable_requests(ctx, type_of='blacklisted'), url_or_index, type_of='blacklisted')


    @staticmethod
    async def remove_requests(ctx, mutable_requests, url_or_index, type_of='requests'):
        target = None

        if isinstance(url_or_index, int):
            if len(mutable_requests) < (url_or_index - 1):
                return await DeveloperSupportCog.send_smartly(ctx, "Failed; no such index was found.", color=disnake.Colour.brand_red())

            target = mutable_requests[url_or_index - 1]
        else:
            for _ in DeveloperSupportCog.iter_requests(ctx, type_of=type_of):
                if _.get('requested') == url_or_index:
                    target = _
                    break
            
            if target is None:
                return await DeveloperSupportCog.send_smartly(ctx, "No such url found for deletion.", color=disnake.Colour.brand_red())

        if target.get('user_id') != ctx.author.id:
            if not ctx.channel.permissions_for(ctx.author).is_superset(disnake.Permissions.manage_guild):
                return await DeveloperSupportCog.send_smartly(ctx, "Unauthorized; you cannot remove someone else's request without `Manage server` permissions or above.", color=disnake.Colour.brand_red())
        
        mutable_requests.remove(target)
        return await DeveloperSupportCog.send_smartly(ctx, "Removed {0[user]}: {0[requested]!r} from {0[message_url]}".format(target), color=disnake.Colour.brand_green())


    @staticmethod
    def get_mutable_requests(ctx, *, type_of='requests'):
        return ctx.bot.database.get_guild_site_requests(ctx.guild.id).setdefault(type_of, [])

    @staticmethod
    def iter_requests(ctx, *, type_of='requests'):
        yield from DeveloperSupportCog.get_mutable_requests(ctx, type_of=type_of)

    @staticmethod
    def append_request(db, guild_id, user, user_id, message_url, url, *, type_of='requests'):
        return db.get_guild_site_requests(guild_id).setdefault(type_of, []).append(
            {
                'user': user,
                'user_id': user_id,
                'requested': url,
                'message_url': message_url,
            }
        )

    @staticmethod
    async def send_viewer(ctx, requests, title):
        paginator = WrappedPaginator(prefix=f"{title}\n", suffix="", max_size=2000)
        embed_permissions = ctx.channel.permissions_for(ctx.guild.me).is_superset(disnake.Permissions(1 << 14))

        kwargs = {
            'owner': ctx.author,
            'bot': ctx.bot,
            'paginator': paginator,
        }

        if embed_permissions:
            cls = PaginatorEmbedInterface

            embed = disnake.Embed.from_dict({
                'footer': {
                    'text': "For you, {}".format(ctx.author),
                    'icon_url': ctx.author.avatar.url
                },
            })
            embed.color = disnake.Colour.fuchsia()
            kwargs.update(
                {'embed': embed}
            )

        else:
            cls = PaginatorInterface

        inteface = cls(**kwargs)        
        await inteface.add_line("\n".join("{0}. [{1[user]}]({1[message_url]}): {1[requested]}".format(count, request) for count, request in enumerate(requests, 1)) or "Nothing to show here.")

        await inteface.send_to(ctx)

    @staticmethod
    async def send_smartly(ctx: 'commands.Context', message_content, *, footer="For you, {}", color=None):

        embed_permissions = ctx.channel.permissions_for(ctx.guild.me).is_superset(disnake.Permissions(1 << 14))
    
        kwargs = {
            'reference': ctx.message
        }

        if embed_permissions:
            embed = disnake.Embed.from_dict(
                {
                    'description': message_content,
                    'footer': {
                        'text': footer.format(ctx.author),
                        'icon_url': ctx.author.avatar.url
                    },
                }
            )
            embed.color = color or disnake.Colour.random()
            kwargs.update(
                {'embed': embed}
            )
        else:
            kwargs.update(
                {'content': message_content}
            )
        
        return await ctx.send(**kwargs)

    async def cog_after_invoke(self, ctx) -> None:
        return self.ignorables.appendleft(ctx.message.id)