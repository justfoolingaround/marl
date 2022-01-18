from typing import Optional
from async_timeout import asyncio
import disnake
from disnake.ext import commands

from .utils import iter_muted, iter_with_permissions


class RaveServerModeration(commands.Cog):

    def __init__(self, bot) :
        self.bot = bot

    @commands.command(enabled=False)
    @commands.guild_only()
    @commands.has_guild_permissions(manage_roles=True)
    @commands.bot_has_guild_permissions(manage_roles=True)
    async def mute(self, ctx, member: disnake.Member, *, reason: Optional[str]=None):
        """
        Traditional mute.

        Removed due to the recent "timeouts".
        """
        raw_embed = {
            'color': 0xe13636,
            'type': 'rich'
        }

        muted_roles = list(iter_muted(ctx.guild.roles))

        if not muted_roles:
            return await ctx.send("No muted roles found in the server.")

        role = muted_roles.pop(0)

        if role in member.roles:
            return await ctx.send("**{}** already has a muted role.")

        await member.add_roles(role, reason=reason)

        embed = disnake.Embed.from_dict(raw_embed)
        embed.description = "Added {} to {}{}.".format(role.mention, member.mention, "" if not reason else " because {}".format(reason))

        return await ctx.send(embed=embed, reference=ctx.message)

    @commands.command()
    @commands.guild_only()
    @commands.has_guild_permissions(manage_messages=True)
    @commands.bot_has_guild_permissions(manage_messages=True)
    async def purge(self, ctx: 'commands.Context', limit: 'Optional[int]'=0, *members: 'disnake.Member'):

        raw_embed = {
            'color': 0xc03823,
            'type': 'rich',
            'footer': {
                    'text': 'For you, {}'.format(ctx.message.author),
                    'icon_url': ctx.message.author.avatar.url,
                },
            }

        root_embed = disnake.Embed.from_dict(raw_embed)    

        if limit == 0:
            return await ctx.send("Specify a limit for purging.", delete_after=5.0, reference=ctx.message)

        root_embed.description = "Purging {} message(s) from {}.".format(limit, "everyone" if not members else ", ".join("{.mention}".format(_) for _ in members))
        root_message = await ctx.send(embed=root_embed, reference=ctx.message)

        messages = []
        before = None

        check = (lambda _: True) if not members else (lambda _: _.author.id in [member.id for member in members]) 

        constant_update_embed = disnake.Embed.from_dict(raw_embed)

        while (len(messages) < limit) and (before.id if before else 0) != (messages[-1].id if messages else root_message.id):
            before = messages[-1] if messages else root_message
        
            constant_update_embed.description = "Iterating above [this message]({.jump_url}), {} found.".format(before, len(messages))
            await root_message.edit(embed=constant_update_embed)

            async for message in ctx.channel.history(limit=1000, before=before):
                if check(message) and len(messages) < limit:
                    messages.append(message)

                    if len(messages) >= limit:
                        break
        

        if not messages:
            no_messages_embed = disnake.Embed.from_dict(raw_embed)
            no_messages_embed.description = "Could not find messages to bulk delete."

            return await root_message.edit(embed=no_messages_embed) 

        bulk_delete_message_embed = disnake.Embed.from_dict(raw_embed)
        bulk_delete_message_embed.color = 0xc94f39
        bulk_delete_message_embed.description = "Commensing purge on message(s) from [here]({.jump_url}), {} message(s) [below]({.jump_url}) have been selected.".format(root_message, len(messages), messages[-1])

        await root_message.edit(embed=bulk_delete_message_embed)

        def iter_only(l=100):
            non_mutable = messages[:]

            while non_mutable:
                yield non_mutable[:l]
                non_mutable = non_mutable[l:]

        deleted = 0

        for portion in iter_only():
            await ctx.channel.delete_messages(portion)
            deleted += len(portion)
            bulk_delete_message_embed.description = "Deleted **{}**/{} messages, upto [here]({.jump_url}).".format(deleted, len(messages), portion[-1])
            await root_message.edit(embed=bulk_delete_message_embed)

        return await root_message.add_reaction("✅")


    @commands.command()
    @commands.guild_only()
    @commands.has_guild_permissions(manage_messages=True)
    @commands.bot_has_guild_permissions(manage_messages=True)
    async def transfer(self, ctx: 'commands.Context', channel: disnake.TextChannel, *, message: 'Optional[disnake.Message]'=None):
        
        raw_embed = {
            'color': 0x07f491,
            'type': 'rich',
            'footer': {
                    'text': 'Moderated for you, {}'.format(ctx.message.author),
                    'icon_url': ctx.message.author.avatar.url,
                },
            }
        
        
        if message is None:
            if ctx.message.reference is None:
                return await ctx.send("Cannot transfer from unreferenced conversations.")

            try:
                message = await ctx.channel.fetch_message(ctx.message.reference.message_id)
            except disnake.NotFound:
                return await ctx.send("Cannot transfer to a message that could not be resolved.")

        if channel == message.channel:
            return await ctx.send("Cannot transfer to the same channel.")

        sent_messages = await message.channel.history(limit=15, before=message).flatten()

        authors = set()
        temporarily_revoked = set()

        async def revert_after(user, channel, *, t=5.0):
            await asyncio.sleep(t)
            
            overwrite = channel.overwrites_for(user)
            overwrite.send_messages = True

            return await channel.set_permissions(user, overwrite=overwrite)

        for author in (_.author for _ in sent_messages):
            if author.id in authors or author.bot:
                continue

            overwrite = message.channel.overwrites_for(author)
            overwrite.send_messages = False
            disnake.Guild.categories
            try:
                await message.channel.set_permissions(author, overwrite=overwrite)
                ctx.bot.loop.create_task(revert_after(author, message.channel))
                temporarily_revoked.add(author.id)
            except disnake.Forbidden:
                pass
            
            authors.add(author.id)

        transfer_request = disnake.Embed.from_dict(raw_embed)

        transfer_request.description = """\
A channel transfer has been requested as the current conversation diverted from the channel topic and there is a better channel available for such discussions.

Continue conversing in {.mention}.""".format(channel)

        if temporarily_revoked:
            transfer_request.description += """
**Send messages** permissions for {} have been revoked for 5s.
""".format(", ".join("<@!{}>".format(_) for _ in temporarily_revoked))

        await ctx.send(embed=transfer_request)

        in_channel = disnake.Embed.from_dict(raw_embed)
        last_message = sent_messages[-1]
        in_channel.description = "As {0.author.mention} was saying: {0.content}".format(last_message)

        return await channel.send(" ".join("<@!{}>".format(_) for _ in authors), embed=in_channel)

    @commands.command()
    async def moderators(self, ctx: 'commands.Context'):
        """
        Find the roles containing moderation powers in the server.
        """
        return await ctx.reply("Roles in the server with moderation powers are: {}".format(', '.join(_.mention for _ in iter_with_permissions(ctx.guild.roles, permission_value=1 << 13))), allowed_mentions=disnake.AllowedMentions(roles=False))
