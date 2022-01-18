from disnake.ext import commands

from .error_handler import command_error_handler


class BotEvents(commands.Cog):
    
    def __init__(self, bot: 'commands.Bot'):
        self.bot = bot

        self.error_configuration = bot.bot_configuration.get('errors')
    
    @commands.Cog.listener()
    async def on_command_error(self, ctx: 'commands.Context', error):

        if not isinstance(error, commands.CommandError) or not self.error_configuration.get('enabled'):
            return

        message = command_error_handler(error, ignore_404=not self.error_configuration.get('command_not_found'))

        if not message:
            return
        
        in_private = self.error_configuration.get('private')

        if in_private:
            try:
                return await ctx.author.send(content=message, as_embed=True, family='ERROR')
            except:
                return

        return await ctx.send(content=message, as_embed=True, family='ERROR', reference=ctx.message)
