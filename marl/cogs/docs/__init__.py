from .cog import DocumentationCog

def setup(bot):
    bot.add_cog(DocumentationCog(bot))
