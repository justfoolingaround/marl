from disnake.ext import commands


class BotVoice(commands.Cog):
    
    def __init__(self, bot):
        self.bot = bot
        
    @commands.group(invoke_without_command=True)
    async def voice(self, ctx):        
        servers = (await ctx.bot.http_session.get('https://latency.discord.media/rtc')).json()
        regional_data = '\n\n'.join("Region: **{}** \n - {}".format(region.get('region').title(), ', '.join(region.get('ips'))) for region in servers)
        
        return await ctx.send("{0}'s voice is active; here are the nearest Discord voice servers (to {0}'s client): \n\n{1}".format(ctx.bot.user.name, regional_data), as_embed=True, family='DEBUG', reference=ctx.message)
    
    @voice.command()
    @commands.is_owner()
    async def clients(self, ctx: 'commands.Context'):
        voice_clients = ctx.bot.voice_clients
        if not voice_clients:
            return await ctx.send("{} is not connected to any voice channels at the moment.".format(ctx.bot.user.name))
        return await ctx.send("{0} is connected to **{1}** channel{s}, showing the atmost 5 of them: \n\n{2}".format(ctx.bot.user.name, len(voice_clients), '\n\n'.join("- {1} at {0.endpoint_ip} [**{0.guild.id}/{0.channel.id}**]".format(client, 'Idle' if not client.is_playing() else 'Active') for client in voice_clients[:5]), s='s' if len(voice_clients) > 1 else ''), as_embed=True, family='DEBUG', reference=ctx.message)
