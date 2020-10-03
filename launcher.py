import glob
from os import getenv
from traceback import print_exc
import pathlib
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()


class MyBot(commands.Bot):
    def __init__(self, **options):
        super().__init__(command_prefix=commands.when_mentioned_or("/"), **options)
        print("Starting Simple Thread...")
        self.remove_command("help")

        for cog in pathlib.Path("cogs/").glob("*.py"):
            try:
                self.load_extension("cogs." + cog.stem)
                print(f"{cog.stem}.pyは正常に読み込まれました。")
            except:
                print_exc()

    async def on_ready(self):
        user = self.user

        print("logged in as:", str(user), user.id)

    async def on_command_error(self, ctx, error):
        ignore_errors = (commands.CommandNotFound, commands.CheckFailure)
        if isinstance(error, ignore_errors):
            return
        await ctx.send(error)


if __name__ == '__main__':
    bot = MyBot()
    bot.run(getenv("DISCORD_BOT_TOKEN"))
