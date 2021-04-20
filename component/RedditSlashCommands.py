from asyncpraw.reddit import Submission
from discord_slash import cog_ext, SlashContext, SlashCommandOptionType
from discord_slash.utils import manage_commands
from discord_slash.utils.manage_commands import create_choice

from util import debug_guilds
from .MyCog import MyCog
from command.reddit import get_reddit_embed, SubmissionType


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
                           manage_commands.create_option(
                               name="request_info",
                               description="Privately obtain post info",
                               option_type=SlashCommandOptionType.STRING,
                               required=False,
                               choices=[
                                   create_choice(
                                       name="Link",
                                       value="link",
                                   ),
                                   # create_choice(
                                   #     name="Gallery",
                                   #     value="gallery",
                                   # ),
                               ],
                           ),
                       ],
                       guild_ids=debug_guilds(),
                       )
    async def reddit(self, ctx: SlashContext, url: str, request_info: str = None):
        if request_info is None:
            hidden = False
        elif request_info == "link":
            hidden = True
        else:
            await ctx.send(content="Invalid type", hidden=True)
            return
        await ctx.defer(hidden=hidden)

        try:
            submission: Submission = await self.bot.reddit.submission(url=url)
        except:
            await ctx.send(content="Invalid URL", hidden=True)
            return
        if submission.over_18:
            if not ctx.channel.nsfw:
                await ctx.send(content="NSFW submissions must be in an NSFW channel", hidden=True)
                return

        if request_info is None:
            content, embed = await get_reddit_embed(self.bot.reddit, submission)
        elif request_info == "link":
            if SubmissionType.get_submission_type(submission).is_self():
                await ctx.send(content="Post must be a link post", hidden=True)
                return
            content = submission.url
            embed = None
        else:
            return  # Already checked earlier
        await ctx.send(content=content, embed=embed, hidden=hidden)
