from disnake.abc import Messageable
from disnake.embeds import Embed
from disnake.ext.commands import Bot, Context


def smart_separation(string: str, max_length, separators=[' ', '\n']):
    if not string:
        return

    if len(string) <= max_length:
        yield string
        return

    separator, separator_index = max(((_, string[:max_length].rfind(_))
                         for _ in separators), key=lambda x: x[1])

    if separator_index == -1:
        separator, separator_index = '', max_length

    yield string[:separator_index]
    yield from smart_separation(string[separator_index + len(separator):], max_length, separators=separators)


class AdjustibleMessageable(Messageable):

    families = {
        'INFO': 0x41b883,
        'DEBUG': 0x3572a5,
        'WARNING': 0xf1e05a,
        'CRITICAL': 0xa21a1e,
        'ERROR': 0xc03723,
    }
    

    async def send(self, content=None, *, embed=None, as_embed=False, family='DEBUG', **kwargs):
        if embed and as_embed:
            raise Exception('embed cannot be set if the message content was set to be sent as an embed itself.')

        limit = 4000
        
        sent = []

        if content:
            for separated in smart_separation(content, max_length=limit):
                if as_embed:
                    sent.append(await super().send(embed=Embed(description=separated, color=self.families.get(family.upper(), 0x3572a5)), **kwargs))
                else:
                    sent.append(await super().send(separated, embed=embed, **kwargs))

            return sent[-1]

        message = await super().send(content=content, embed=embed, **kwargs)
        return message

class AdjustibleContext(Context, AdjustibleMessageable):
    bot: Bot
