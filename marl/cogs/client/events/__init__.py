from .cog import BotEvents

def setup(bot):
    bot.add_cog(BotEvents(bot))