from disnake import AllowedMentions, Intents
from marl.bot import MarlBot

bot = MarlBot(intents=Intents.all(), allowed_mentions=AllowedMentions(everyone=False, roles=True))

for cog in [
            'jishaku',
            'marl.cogs.client.events',
            'marl.cogs.client.base',
            'marl.cogs.moderation',
            'marl.cogs.antiraid',
            'marl.cogs.petpet',
            'marl.cogs.kotlinc',
            ]:
    bot.load_extension(cog)

bot.run()