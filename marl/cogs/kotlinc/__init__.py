"""
Run Kotlin scripts, using the official API.
"""


from .cog import KtCog

def setup(bot):
    bot.add_cog(KtCog(bot))
