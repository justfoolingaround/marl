import disnake
from disnake.ext import commands

from .utils import (URL_REGEX, iter_every_text_segment, iter_likely_staffs,
                    iter_muted, iter_with_permissions)


class AntiRaidCog(commands.Cog):

    DATABASE = 'https://raw.githubusercontent.com/nikolaischunk/discord-phishing-links/main/domain-list.json'

    def __init__(self, bot) :
        self.bot = bot
        
        self.banned_hosts = []

    @commands.Cog.listener('on_ready')
    async def on_bot_load(self):
        self.banned_hosts = (await self.bot.http_session.get(self.DATABASE)).json().get('domains')


    @commands.Cog.listener('on_message')
    async def banned_hosts_action(self, message: 'disnake.Message') -> None:
        
        if (not message.guild) or message.author.bot or message.author.id == self.bot.user.id:
            return
        
        blacklisted_hosts = []

        for text_segment in iter_every_text_segment(message):
            for url in (_.group(0) for _ in URL_REGEX.finditer(text_segment)):
                if any(banned_host.endswith(url) for banned_host in self.banned_hosts):
                    blacklisted_hosts.append(url)
        
        if not blacklisted_hosts:
            return
        
        embed = disnake.Embed.from_dict({
            'footer': {
                'text': 'Moderating you, {}'.format(message.author),
                'icon_url': message.author.avatar.url,
            },
            'color': disnake.Colour.brand_red().value,
            'type': 'rich'
        })

        embed.description = "Hey {0.author.mention}, your message contains one or more blacklisted hosts.".format(message)

        moderation_steps = []
        muted_roles = list(iter_muted(message.guild.roles))
        handler_roles = list(iter_with_permissions(message.guild.roles, permission_value=1 << 28))
        mentions = ", ".join(_.mention for _ in set(handler_roles + list(iter_likely_staffs(message.guild.roles))) if _.mentionable)

        try:
            await message.delete()
        except disnake.Forbidden:
            moderation_steps.append("• Delete user message.")
        except disnake.NotFound:
            pass

        if not muted_roles:
            moderation_steps.append("• Create a muted role and assign it to the guilty.")
        else:
            moderation_steps.append("• Assign a muted role (i.e. {}) to the guilty.".format(', '.join(_.mention for _ in muted_roles)))

        if not handler_roles:
            moderation_steps.append("• Create a role that can assign roles.")
        else:
            moderation_steps.append("({} can manage user roles in the server.)".format(', '.join(_.mention for _ in handler_roles)))

        if not mentions:
            moderation_steps.append("• Create a mentionable moderator role for contacting **you**.")

        embed.add_field("Blacklisted hosts", "\n".join(blacklisted_hosts), inline=False)
        embed.add_field("Suggested moderation steps", "\n".join(moderation_steps), inline=False)

        return await message.channel.send(content=mentions, embed=embed)
