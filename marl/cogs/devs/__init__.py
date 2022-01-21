from .cog import DeveloperSupportCog

def setup(bot):
    bot.add_cog(DeveloperSupportCog(bot))
