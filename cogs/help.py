from textwrap import dedent

from discord.ext import commands


class Help(commands.Cog, command_attrs=dict(hidden=True)):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def help(self, ctx):
        await ctx.send(
            dedent(
                """\
            # Simple Highlight は Discord サーバーにハイライト機能を実装する bot です。

            # 使い方
            `/set (<HighlightChannel>)`
            ハイライトを送るチャンネルを設定します。
            
            `/remove`
            ハイライト機能を削除します。チャンネルは削除されません。

            # GitHubはこちら
            <https://github.com/tenzyu/simple-quote>

            # サポートサーバーはこちら
            <https://discord.gg/4nSKCE9RRn>
            """
            )
        )


def setup(bot):
    bot.add_cog(Help(bot))
