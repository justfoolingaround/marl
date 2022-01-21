import disnake
import httpx
import regex
from disnake.ext import commands
from jishaku.codeblocks import codeblock_converter
from jishaku.exception_handling import ReactionProcedureTimer
from jishaku.paginators import (PaginatorEmbedInterface, PaginatorInterface,
                                WrappedPaginator)

IN_PACKAGE_REGEX = regex.compile(r"fun\s+main\(.*?\)\s*{.*?}", regex.S)

class KtCog(commands.Cog):
    
    KOTLIN_VERSION = "1.6.10"
    API_URL = "https://api.kotlinlang.org//api/{}/compiler/run".format(KOTLIN_VERSION)

    def __init__(self, bot: 'commands.Bot'):
        self.bot = bot

        self.event_mapping: 'dict[int, PaginatorEmbedInterface]' = dict()
        self.http_session = httpx.AsyncClient()

    @staticmethod
    def merge_errors(errors):
        """
        A subtle merge of all the errors that follow each other
        but are separated by the API, for some reason.
        """
        def extract(cls, *attrs):
            return *(cls.get(attr) for attr in attrs),

        pending_merge = None

        for error in errors:
            
            interval, *constituents = extract(error, "interval", "message", "severity")

            if pending_merge is None:
                pending_merge = (interval, *constituents)
                continue
            
            (p_interval, *p_constituents) = pending_merge

            if p_constituents != constituents:
                yield pending_merge
                pending_merge = (interval, *constituents)
                continue
            
            p_start = p_interval.get('start')
            p_end = p_interval.get('end')

            start = interval.get('start')
            end = interval.get('end')

            if (p_end.get('line'), p_end.get('ch')) > (start.get('line'), start.get('ch')):
                pending_merge = ({'start': p_start, 'end': end}, *p_constituents)
            else:
                yield pending_merge
                pending_merge = None
        
        if pending_merge is not None:
            yield pending_merge

            
    async def run(self, code):
        """
        Run the Kotlin code.
        """
        api_response = await self.http_session.post(
            self.API_URL,
            json={
                'files': [
                    {
                        'name': "OutFile.kt",
                        'text': code,
                    }
                ]
            }
        )

        content = api_response.json()

        stdout = content.get('text', '')[11:-12]
        errors = ("\n".join("[{0} {2[start][line]}:{2[start][ch]}-{2[end][line]}:{2[end][ch]}] {1}".format(severity, message, interval) for interval, message, severity in self.merge_errors(content.get('errors', {}).get('OutFile.kt', []))))
        
        return (
            api_response,
            stdout, 
            errors,
            content.get('exception')
        )

    @commands.group('kt', aliases=['kotlin'], invoke_without_command=True)
    async def kotlin_execution(self, ctx: 'commands.Context', *, code: codeblock_converter):

        kotlin_code = code.content.strip()

        if not IN_PACKAGE_REGEX.search(kotlin_code):
            kotlin_code = "fun main() {{{}}}".format(kotlin_code)

        paginator = WrappedPaginator(prefix="```kt", suffix="``` \nKotlin v{}".format(self.KOTLIN_VERSION), max_size=2000)

        if ctx.guild:
            embed_permissions = ctx.channel.permissions_for(ctx.guild.me).is_superset(disnake.Permissions(1 << 14))
        else:
            embed_permissions = True

        kwargs = {
            'owner': ctx.author,
            'bot': ctx.bot,
            'paginator': paginator,
        }

        if embed_permissions:
            cls = PaginatorEmbedInterface

            embed = disnake.Embed.from_dict({
                'footer': {
                    'text': "Compiling for you, {}".format(ctx.author),
                    'icon_url': ctx.author.avatar.url
                },
            })
            embed.color = disnake.Colour.purple()
            kwargs.update(
                {'embed': embed}
            )

        else:
            cls = PaginatorInterface

        async with ReactionProcedureTimer(ctx.message, loop=ctx.bot.loop):
            interface = cls(**kwargs) 
            await interface.add_line('\n'.join("[run] {}".format(_) for _ in kotlin_code.splitlines()))

            await interface.send_to(ctx)

            _, stdout, errors, exceptions = await self.run(kotlin_code)

            await interface.add_line(empty=True)
            await interface.add_line("\n".join("[stdout] {}".format(_) for _ in stdout.splitlines()))
            
            if errors:
                await interface.add_line(empty=True)
                await interface.add_line(errors.strip())
            
            if exceptions:
                await interface.add_line("[exception] {}".format(exceptions))

        self.event_mapping.update({ctx.message.id: interface})


    @commands.Cog.listener()
    async def on_message_edit(self, before, after):

        if after.id not in self.event_mapping:
            return

        interface = self.event_mapping.get(after.id)
        await interface.button_close.callback(None)

        ctx = await self.bot.get_context(after)
        return await self.bot.invoke(ctx)

    @commands.Cog.listener()
    async def on_message_delete(self, deleted_message):
        if deleted_message.id not in self.event_mapping:
            return

        interface = self.event_mapping.get(deleted_message.id)
        await interface.button_close.callback(None)

        del self.event_mapping[deleted_message.id]
