from textwrap import dedent

from discord.ext import commands


class Help(commands.Cog, command_attrs=dict(hidden=True)):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def help(self, ctx):
        await ctx.send(dedent("""\
            **Simple Highlight** allows you to implement Highlight feature.

            > `/set`
            Sets the highlight to channel where a message sent.

            > `/remove`
            Removes the Highlight feature.

            See also GitHub for more information:
            https://github.com/tenzyu/simple-highlight
            """))


def setup(bot):
    bot.add_cog(Help(bot))
