from .cog import RaveServerModeration

def setup(bot):
    bot.add_cog(RaveServerModeration(bot))