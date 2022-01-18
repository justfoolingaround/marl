"""
A powerful anti-raid that will protect servers from attacks
from mass bot accounts.

This cog leaves the final action to a responsible moderator
to accout for false positives or testing sessions.

As of 2022-01-18, only a single anti-raid feature remains
which is anti-scam.

This is done because the piece of code of the previous
anti-raid does not belong to the owner of the repository and
the owner is not permitted to use the code publicly.

The current code belongs to KR@justfoolingaround.
"""

from .cog import AntiRaidCog

def setup(bot):
    bot.add_cog(AntiRaidCog(bot))