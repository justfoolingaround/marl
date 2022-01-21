from disnake import AllowedMentions, Intents
from marl.bot import MarlBot
import os

bot = MarlBot(intents=Intents.all(), allowed_mentions=AllowedMentions(everyone=False, roles=True))

for cog in [
            'jishaku',
            'marl.cogs.client.events',
            'marl.cogs.client.base',
            'marl.cogs.moderation',
            'marl.cogs.antiraid',
            'marl.cogs.petpet',
            'marl.cogs.kotlinc',
            'marl.cogs.devs',
            ]:
    bot.load_extension(cog)

@bot.event
async def on_ready():
    webhook = bot.bot_configuration.get('status', {})
    webhook_url = webhook.get('webhook_url')
    if webhook.get('env'):
        webhook_url = os.getenv(webhook_url)

    await bot.http_session.post(webhook_url, json={'content': 'Marl has loaded.'})

bot.run()
