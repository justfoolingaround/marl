from .cog import PetPetGenerator

def setup(bot):
    bot.add_cog(PetPetGenerator(bot))