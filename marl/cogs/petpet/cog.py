import asyncio
import io
from typing import Optional, Union

import disnake
from disnake.ext import commands

from .utils import make, get_circular_fit


class PetPetGenerator(commands.Cog):

    def __init__(self, bot) :
        self.bot = bot

    @staticmethod
    async def get_image(image_source, delay):
        if isinstance(image_source, disnake.PartialEmoji):
            image_source = io.BytesIO(await image_source.read())

        if isinstance(image_source, disnake.Member):
            image_source = io.BytesIO(await (image_source.avatar or image_source.default_avatar).read())
        
        loop = asyncio.get_running_loop()
        
        circular_image = await loop.run_in_executor(None, get_circular_fit, image_source)
        final_image = io.BytesIO()
        
        await loop.run_in_executor(None, lambda: make(circular_image, final_image, delay=delay))
        
        final_image.seek(0)
        
        return final_image

    @commands.group(invoke_without_command=True)
    async def petpet(self, ctx: 'commands.Context', image_source: 'Union[disnake.PartialEmoji, disnake.Member]', delay: 'Optional[int]'=30):
        if delay < 20:
            return await ctx.send("Delay cannot be less than 20.", reference=ctx.message)
        
        if delay > 70:
            return await ctx.send("Delay cannot be greater than 70.", reference=ctx.message)
        
        return await ctx.send(file=disnake.File(await self.get_image(image_source, delay), "petpet.gif"), reference=ctx.message)
    
    @petpet.command('emote', aliases=['emoji'])
    @commands.guild_only()
    @commands.has_permissions(manage_emojis=True)
    @commands.bot_has_permissions(manage_emojis=True)
    async def petpet_emote(self, ctx: 'commands.Context', image_source: 'Union[disnake.PartialEmoji, disnake.Member]', name: 'Optional[str]'=None, delay: 'Optional[int]'=30):

        if delay < 20:
            return await ctx.send("Delay cannot be less than 20.", reference=ctx.message)
        
        if delay > 70:
            return await ctx.send("Delay cannot be greater than 70.", reference=ctx.message)
                
        image = await self.get_image(image_source, delay)

        if name is None:
            if isinstance(image_source, disnake.PartialEmoji):
                name = image_source.name

            if isinstance(image_source, disnake.Member):
                name = image_source.display_name

        if not name.lower().startswith('pet'):
            name = "pet{}".format(name)

        emote = await ctx.guild.create_custom_emoji(name=name, image=image.read(), reason="{} used the petpet upload command.".format(ctx.author))

        return await ctx.send("Uploaded `{}` as {}.".format(name, emote), allowed_mentions=disnake.AllowedMentions(users=False, roles=False, everyone=False))
