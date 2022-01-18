import httpx
from disnake.ext import commands
from importlib_metadata import os

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
    
    def __init__(self, help_command=None, description=None, **options):

        prefix_conf = self.bot_configuration.get('prefix')

        if prefix_conf.get('when_mentioned'):
            prefix = commands.when_mentioned_or(*prefix_conf.get('values', []))
        else:
            prefix = lambda: prefix_conf.get('values', [])

        super().__init__(prefix, help_command, description, **options)

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
    
    async def process_commands(self, message):
        return await self.invoke(await self.get_context(message, cls=AdjustibleContext))
