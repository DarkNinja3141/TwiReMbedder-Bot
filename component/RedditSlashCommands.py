from discord_slash import cog_ext, SlashContext, SlashCommandOptionType
from discord_slash.utils import manage_commands

from .MyCog import MyCog


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
        submission = await self.bot.reddit.submission(url=url)
        await ctx.send(submission.title)
