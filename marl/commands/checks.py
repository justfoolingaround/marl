from disnake.ext import commands


def predicate_is_bot_administrator(ctx: 'commands.Context', *, error_out=True):

    if ctx.bot.is_owner(ctx.author) or (ctx.author.id in ctx.bot.database.get_global_administrators()):
        return True
    
    if error_out:
        raise commands.CheckFailure("Unauthorized; only bot administrators can use this command.")


def predicate_is_divine(ctx: 'commands.Context', *, error_out=True):

    if predicate_is_bot_administrator(ctx, error_out=False):
        return True

    divines = ctx.bot.database.get_global_divine()

    if (ctx.author.id in divines.get('users', [])) or ctx.guild and (ctx.guild in divines.get('guilds', []) or ctx.guild.owner_id in divines.get('users')):
        return True

    if error_out:
        raise commands.CheckFailure("Unauthorized; only divine bot users and above can use this command.")


def predicate_is_trusted(ctx: 'commands.Context', *, error_out=True):
    
    if predicate_is_divine(ctx, error_out=False):
        return True

    trusted = ctx.bot.database.get_global_trusted()

    if (ctx.author.id in trusted.get('users', [])) or ctx.guild and (ctx.guild in trusted.get('guilds', []) or ctx.guild.owner_id in trusted.get('users')):
        return True

    if error_out:
        raise commands.CheckFailure("Unauthorized; only trusted bot users and above can use this command.")
