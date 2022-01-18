from .cog import BotVoice

def setup(bot):
    bot.add_cog(BotVoice(bot))