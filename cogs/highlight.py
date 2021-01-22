import sqlite3
from textwrap import dedent

import discord
from discord.ext import commands


def get_db(db):
    return sqlite3.connect(f"database/{db}")


async def count_meaningful_reactions(message):
    reaction_count = 0
    for reaction in message.reactions:
        reaction_count += reaction.count
        users = await reaction.users().flatten()
        if message.author in users:
            reaction_count -= 1
        bots = [user for user in users if user.bot]
        reaction_count -= len(bots)
    return reaction_count


class Highlight(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.guild_db = get_db("guild.db")
        self.message_db = get_db("message.db")

        with self.guild_db:
            c = self.guild_db.cursor()
            c.execute(
                """
                CREATE TABLE IF NOT EXISTS guild(
                    guild_id bigint PRIMARY KEY,
                    highlight_channel_id bigint,
                    notice_reaction_count text
                )
            """
            )

        with self.message_db:
            c = self.message_db.cursor()
            c.execute(
                """
                CREATE TABLE IF NOT EXISTS message(
                    message_id bigint PRIMARY KEY,
                    max_reaction_count int
                )
            """
            )

    def find_highlight_channel(self, guild_id):
        sql = """
            SELECT *
                FROM guild
                WHERE guild_id = ?
            """
        val = (guild_id,)
        with self.guild_db:
            c = self.guild_db.cursor()
            c.execute(sql, val)
            return c.fetchone()

    def find_message_data(self, message_id):
        sql = """
            SELECT *
                FROM message
                WHERE message_id = ?
            """
        val = (message_id,)
        with self.message_db:
            c = self.message_db.cursor()
            c.execute(sql, val)
            return c.fetchone()

    @commands.command(name="set")
    @commands.has_guild_permissions(administrator=True)
    async def _set(self, ctx, channel: discord.TextChannel = None):
        if ctx.author.bot:
            return

        if not channel:
            channel = ctx.channel

        guild_id = ctx.message.guild.id
        channel_id = channel.id

        response = self.find_highlight_channel(guild_id)
        if not response:
            default_notice_count = (
                "5,10,20,30,40,50,60,70,80,90,100,200,300,400,500,600,700,800,900,1000"
            )
            sql = """
                INSERT
                    INTO guild (guild_id, highlight_channel_id, notice_reaction_count)
                    VALUES (?,?,?)
                """
            val = (guild_id, channel_id, default_notice_count)
            text = f"Highlight Channel has been set to {channel.mention}"
        else:
            sql = """
                UPDATE guild
                    SET highlight_channel_id = ?
                    WHERE guild_id = ?
                """
            val = (channel_id, guild_id)
            text = f"Highlight Channel has been updated to {channel.mention}"
        with self.guild_db:
            c = self.guild_db.cursor()
            c.execute(sql, val)
        await ctx.send(text)

    @commands.command(aliases=["rem"])
    @commands.has_guild_permissions(administrator=True)
    async def remove(self, ctx):
        if ctx.author.bot:
            return

        guild_id = ctx.message.guild.id

        response = self.find_highlight_channel(guild_id)
        if not response:
            await ctx.send("This server is not registered!")
            return
        sql = """
            DELETE
                FROM guild
                WHERE guild_id = ?
            """
        val = (guild_id,)

        with self.guild_db:
            c = self.guild_db.cursor()
            c.execute(sql, val)

        await ctx.send(f"{ctx.channel.mention} has been removed.")

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, reaction: discord.RawReactionActionEvent):
        channel = self.bot.get_channel(reaction.channel_id)
        message_id = reaction.message_id
        message = await channel.fetch_message(message_id)
        if reaction.member == message.author:
            return

        guild_id = message.guild.id
        guild_data = self.find_highlight_channel(guild_id)
        if not guild_data:
            return

        count = await count_meaningful_reactions(message)
        message_data = self.find_message_data(message_id)
        if not message_data:
            sql = """
                INSERT
                    INTO message (message_id, max_reaction_count)
                    VALUES (?,?)
                """
            val = (message_id, count)
        # 1 as max_reaction_count
        elif count <= message_data[1]:
            return
        else:
            sql = """
                UPDATE message
                    SET max_reaction_count = ?
                    WHERE message_id = ?
                """
            val = (count, message_id)
        with self.message_db:
            c = self.message_db.cursor()
            c.execute(sql, val)

        # 2 as notice_reaction_count
        notice_reaction_counts = guild_data[2].split(",")
        if not str(count) in notice_reaction_counts:
            return

        ch_highlight = self.bot.get_channel(guild_data[1])

        highlight_msg = dedent(
            f"""\
                :tada: ** {count} REACTIONS! ** :tada:
                {message.author.display_name}'s message got {count} reactions! 
            """
        )

        # If Highlight from NSFW to SFW
        if message.channel.is_nsfw() and not ch_highlight.is_nsfw():
            embed = discord.Embed(
                title="**Highlight from NSFW**",
                url=message.jump_url,
                description="click to view messageUrl",
                timestamp=message.created_at,
            )
            embed.set_footer(text="#NSFW")
            await ch_highlight.send(highlight_msg, embed=embed)
            return

        # If no messages
        if len(message.content) == 0:

            if message.attachments:
                if message.attachments[0].is_spoiler():
                    fixed_file = await message.attachments[0].to_file(spoiler=True)
                    await ch_highlight.send(highlight_msg, file=fixed_file)
                else:
                    embed = discord.Embed(
                        title="#" + message.channel.name,
                        url=message.jump_url,
                        timestamp=message.created_at,
                    )
                    embed.set_author(
                        name=message.author.display_name,
                        icon_url=message.author.avatar_url,
                    )
                    embed.set_footer(text="#" + message.channel.name)
                    embed.set_image(url=message.attachments[0].url)
                    await ch_highlight.send(highlight_msg, embed=embed)
            if message.embeds:
                for embed in message.embeds:
                    await ch_highlight.send(highlight_msg, embed=embed)
            return

        embed = discord.Embed(
            title="#" + message.channel.name,
            url=message.jump_url,
            description=message.content,
            timestamp=message.created_at,
        )
        embed.set_author(
            name=message.author.display_name, icon_url=message.author.avatar_url
        )
        embed.set_footer(text="#" + message.channel.name)
        fixed_file = None
        if message.attachments:
            if message.attachments[0].is_spoiler():
                fixed_file = await message.attachments[0].to_file(spoiler=True)
            else:
                embed.set_image(url=message.attachments[0].url)

        await ch_highlight.send(
            highlight_msg,
            embed=embed,
            file=fixed_file,
        )
        if message.embeds:
            await ch_highlight.send("────────")
            for embed in message.embeds:
                await ch_highlight.send(embed=embed)


def setup(bot):
    bot.add_cog(Highlight(bot))
