from .cog import BotBase

def setup(bot):
    bot.add_cog(BotBase(bot))