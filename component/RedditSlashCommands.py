from asyncpraw.exceptions import InvalidURL
from asyncpraw.reddit import Submission
from discord_slash import cog_ext, SlashContext, SlashCommandOptionType
from discord_slash.utils import manage_commands

from .MyCog import MyCog
from command.reddit import get_reddit_embed


class RedditSlashCommands(MyCog):
    def __init__(self, bot):
        super().__init__(bot)

    @cog_ext.cog_slash(name="reddit",
                       description="Display a Reddit post",
                       options=[
                           manage_commands.create_option(
                               name="url",
                               description="URL of the Reddit post",
                               option_type=SlashCommandOptionType.STRING,
                               required=True,
                           ),
                       ])
    async def reddit(self, ctx: SlashContext, url: str):
        try:
            submission: Submission = await self.bot.reddit.submission(url=url)
        except InvalidURL:
            await ctx.send(content="Invalid URL", hidden=True)
            return
        if submission.over_18:
            if not ctx.channel.nsfw:
                await ctx.send(content="NSFW submissions must be in an NSFW channel", hidden=True)
                return

        content, embed = await get_reddit_embed(self.bot.reddit, submission)
        await ctx.send(content=content, embed=embed)
