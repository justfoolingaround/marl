import time
from datetime import datetime

import disnake
from disnake.ext import commands


class BotBase(commands.Cog):
    
    ping_lock = set()

    def __init__(self, bot: 'commands.Bot'):
        self.bot = bot
        
    @commands.Cog.listener('on_ready')
    async def on_bot_ready(self):
        self.activation_time = datetime.now()

    @staticmethod
    def ping_color(rtt_ms=None):
        if rtt_ms is None:
            return disnake.Colour.fuchsia()

        if rtt_ms < 20:
            return disnake.Colour.green()
        
        if rtt_ms < 100:
            return disnake.Colour.yellow()
        
        if rtt_ms < 150:
            return disnake.Colour.orange()

        if rtt_ms < 200:
            return disnake.Colour.dark_orange()

        if rtt_ms < 500:
            return disnake.Colour.brand_red()
        
        return disnake.Colour(0)
        
    @staticmethod
    def data_evaluation(datas: 'tuple[float]'):
        """
        Returns the average and the standard deviations of data.
        """
        if not datas:
            return 0.0, 0.0
        
        average = sum(datas) / len(datas)
        
        if len(datas) > 1:
            return average, (sum((data - average)**2 for data in datas) / (len(datas) - 1))**.5     
        
        return average, 0.0
            
    
    @commands.command()
    async def ping(self, ctx: 'commands.Context'):
        """
        Ping from the bot to Discord. 
        """
        
        if ctx.channel.id in self.ping_lock:
            return await ctx.message.add_reaction("\N{WARNING SIGN}")

        self.ping_lock.add(ctx.channel.id)

        text_content = ["Pinging from {.bot.user.name} to Discord".format(ctx), ""]

        embed = disnake.Embed.from_dict({
            'color': self.ping_color().value,
            'footer': {
                'text': "Pinging for you, {}".format(ctx.author),
                'icon_url': (ctx.author.guild_avatar or ctx.author.avatar).url,
            }
        })

        embed.description = '\n'.join(text_content).strip()
        message = None

        latencies = []
        websocket_latencies = []

        for count in range(1, 7):
            
            fore = time.perf_counter()

            if message is None:
                message = await ctx.send(embed=embed, reference=ctx.message, allowed_mentions=disnake.AllowedMentions(users=False))
            else:
                message = await message.edit(embed=embed, allowed_mentions=disnake.AllowedMentions(users=False))
            
            rtt = (time.perf_counter() - fore) * 1e3

            text_content.append(
                "Reading {}: **RTT** `{:.02f}`ms".format(count, rtt)
            )

            latencies.append(rtt)

            if ctx.bot.latency > 0:
                websocket_latencies.append(ctx.bot.latency)
            
            rtt_avg, rtt_stddev = self.data_evaluation(latencies)
            ws_avg, ws_stddev = self.data_evaluation(websocket_latencies)


            embed.description = "\n".join(text_content).strip() + """

Average **RTT**: {:.02f} ± {:.02f}
Average Websocket Latency: {:.02f} ± {:.02f}""".format(
    rtt_avg, rtt_stddev,
    ws_avg, ws_stddev,
)
            embed.colour = self.ping_color(rtt_avg).value

        self.ping_lock.remove(ctx.channel.id)
