"""
A super simple documentation Cog for development needs.
"""

import disnake
import httpx
from disnake.ext import commands
from jishaku.paginators import (PaginatorEmbedInterface, PaginatorInterface,
                                WrappedPaginator)

from .inventory import SphinxInventoryIO


class DocumentationCog(commands.Cog):

    DOCUMENTATION_URLS = (
        'https://docs.python.org/3/',
        'https://docs.disnake.dev/en/latest/',
        'https://docs.aiohttp.org/en/stable/',
    )

    def __init__(self, bot):
        self.bot = bot
        self.session = httpx.AsyncClient()

        self.inventories = []

    async def cog_load(self):
        self.inventories = [await SphinxInventoryIO.get_inventory(self.session, url) for url in self.DOCUMENTATION_URLS]


    @commands.command()
    async def docs(self, ctx, *, query: 'str'):
        """
        Search the documentation for a query.
        """
        results = {}

        for inventory in self.inventories:
            out = list(inventory.search(query))
            if out:
                results["[{0.project_name}]({0.source}) v{0.project_version}".format(inventory)] = out, inventory

        if not results:
            return await self.send_smartly(ctx, 'No documentation reference found.', color=disnake.Color.brand_red())

        return await self.send_smartly(ctx, "\n\n".join("`{}` {}: \n{}".format(stem_count, project, '\n'.join("`{}.{}` [**`{}`**]({}/{})".format(stem_count, branch_count, entry, inventory.source.rstrip('/'), location) for branch_count, (entry, location) in enumerate(result, 1))) for stem_count, (project, (result, inventory)) in enumerate(results.items(), 1)), title="Viewing inventory entries for `{}`".format(query), color=disnake.Color.brand_green())


    @commands.group(invoke_without_command=True)
    @commands.is_owner()
    async def inventory(self, ctx):
        """
        View the current inventories.
        """
        return await self.send_smartly(ctx, '\n'.join('[{0.project_name}]({0.source}) v{0.project_version}: {1} entries'.format(inventory, len(inventory.entries)) for inventory in self.inventories) or "No inventories loaded at the moment.")

        
    @staticmethod
    async def send_viewer(ctx, content, *, color=None, title=None):
        paginator = WrappedPaginator(prefix="", suffix="", max_size=2000)
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

            if title is not None:
                embed.title = title

            embed.color = color or disnake.Colour.fuchsia()
            kwargs.update(
                {'embed': embed}
            )

        else:
            cls = PaginatorInterface

        inteface = cls(**kwargs)

        await inteface.add_line(content)
        return await inteface.send_to(ctx)

    @staticmethod
    async def send_smartly(ctx: 'commands.Context', message_content, *, footer="For you, {}", color=None, title=None):

        if len(message_content) > 1500:
            return await DocumentationCog.send_viewer(ctx, message_content, title=title, color=color)

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

            if title is not None:
                embed.title = title

            embed.color = color or disnake.Colour.random()
            kwargs.update(
                {'embed': embed}
            )
        else:
            kwargs.update(
                {'content': message_content}
            )
        
        return await ctx.send(**kwargs)
