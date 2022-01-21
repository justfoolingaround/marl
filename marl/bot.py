import os
import signal

import httpx
from disnake.ext import commands

from marl.database.json_db import MarlDatabase

from .commands import AdjustibleContext
from .helpers.configuration import get_configuration


class Color(object):
    error = 0xff0000


class MarlBot(commands.Bot):
    """
    A cool discord bot.
    """
    
    color = Color()
    
    configuration = get_configuration()

    bot_configuration = configuration.get('bot', {})
    error_when_cnf = bot_configuration.get('command_not_found')
    
    database = MarlDatabase('./marl-db/marl-db.json')

    def __init__(self, help_command=None, description=None, **options):

        prefix_conf = self.bot_configuration.get('prefix')

        if prefix_conf.get('when_mentioned'):
            prefix = commands.when_mentioned_or(*prefix_conf.get('values', []))
        else:
            prefix = lambda: prefix_conf.get('values', [])

        super().__init__(prefix, help_command, description, **options)

    async def get_prefix(self, message):

        if message.guild:
            guild_prefix = self.database.get_guild_prefix(message.guild.id)
            if guild_prefix is not None:
                return await commands.when_mentioned_or(guild_prefix)(self, message)

        return await super().get_prefix(message)

    async def start(self, *, reconnect=True, session=None):
        """
        Override for .start async method for adding a httpx session to the bot.
        """
        token = self.bot_configuration.get('token')

        if self.bot_configuration.get('env'):
            token = os.getenv(token)
        
        self.http_session = session or httpx.AsyncClient()
        return await super().start(token, reconnect=reconnect)

    async def close(self):
        """
        Override for .close async method for closing the httpx session of the bot.
        """
        return await self.http_session.aclose() and await super().close()

    def blacklisted(self, message):
        blacklist = self.database.get_global_blacklist()
        state = blacklist.setdefault('inverse', False)

        invoke = True

        if message.guild:
            if message.guild.id in blacklist.setdefault('guilds', []) or message.guild.owner_id in blacklist.setdefault('users', []):
                invoke = False

        if message.author.id in blacklist.setdefault('users', []):
            invoke = False

        if invoke:
            if state:
                """The command is in the blacklist and the state is blacklist."""
                return True
        else:
            if not state:
                """The command is not in the blacklist but the state is whitelist."""
                return True
        
        return False


    async def process_commands(self, message):
        if self.blacklisted(message):
            return
        
        return await self.invoke(await self.get_context(message, cls=AdjustibleContext))


signal.signal(signal.SIGTERM, lambda *args, **kwargs: MarlBot.database.save() or exit())
signal.signal(signal.SIGINT, lambda *args, **kwargs: MarlBot.database.save() or exit())
