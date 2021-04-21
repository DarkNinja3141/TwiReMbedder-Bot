from asyncpraw.reddit import Submission
from discord_slash import cog_ext, SlashContext, SlashCommandOptionType
from discord_slash.utils import manage_commands
from discord_slash.utils.manage_commands import create_choice

from util import debug_guilds
from util.error import CommandUseFailure
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
                                   create_choice(
                                       name="Clean URL",
                                       value="url",
                                   ),
                                   create_choice(
                                       name="Short URL",
                                       value="shortlink",
                                   ),
                               ],
                           ),
                       ],
                       guild_ids=debug_guilds(),
                       )
    async def reddit(self, ctx: SlashContext, url: str, request_info: str = None):
        hidden = request_info is not None
        await ctx.defer(hidden=hidden)

        try:
            submission: Submission = await self.bot.reddit.submission(url=url)
        except:
            raise CommandUseFailure("Invalid URL")
        if submission.over_18:
            if not ctx.channel.nsfw:
                raise CommandUseFailure("NSFW submissions must be in an NSFW channel")

        embed = None
        if request_info is None:
            content, embed = await get_reddit_embed(self.bot.reddit, submission)
        elif request_info == "link":
            if SubmissionType.get_submission_type(submission).is_self():
                raise CommandUseFailure("Post must be a link post")
            content = submission.url
        elif request_info == "url":
            content = f"https://www.reddit.com{submission.permalink}"
        elif request_info == "shortlink":
            content = submission.shortlink
        else:
            raise CommandUseFailure("Invalid request_info string")
        await ctx.send(content=content, embed=embed, hidden=hidden)
