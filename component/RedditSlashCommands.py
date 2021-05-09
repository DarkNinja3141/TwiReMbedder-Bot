import discord
from asyncpraw.reddit import Submission
from discord_slash import cog_ext, SlashContext, SlashCommandOptionType
from discord_slash.model import SlashMessage
from discord_slash.utils import manage_commands
from discord_slash.utils.manage_commands import create_choice

from command.video import do_reddit_video_download
from util import *
from util.error import CommandUseFailure
from .MyCog import MyCog
from command.reddit import SubmissionType, get_reddit_embed, get_reddit_poll_embed, get_reddit_gallery_embed, \
    request_info_gallery, request_info_poll, get_reddit_video_embed


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
                                   create_choice(
                                       name="Clean URL",
                                       value="url",
                                   ),
                                   create_choice(
                                       name="Short URL",
                                       value="shortlink",
                                   ),
                                   create_choice(
                                       name="Gallery",
                                       value="gallery",
                                   ),
                                   create_choice(
                                       name="Poll",
                                       value="poll",
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
            setattr(submission, "submission_type", SubmissionType.get_submission_type(submission))
        except:
            raise CommandUseFailure("Invalid URL")
        if submission.over_18:
            if not ctx.channel.nsfw:
                raise CommandUseFailure("NSFW submissions must be in an NSFW channel")

        embed = embeds = None
        do_video_upload = False
        if request_info is None:
            content, embed = await get_reddit_embed(self.bot.reddit, submission)
            poll_embed = await get_reddit_poll_embed(self.bot.reddit, submission)
            if poll_embed is not None:
                embeds = [embed, poll_embed]
                embed = None
            gallery_embed = await get_reddit_gallery_embed(self.bot.reddit, submission)
            if gallery_embed is not None:
                embeds = [embed, gallery_embed]
                embed = None
            video_embed = await get_reddit_video_embed(self.bot.reddit, submission)
            if video_embed is not None:
                embeds = [embed, video_embed]
                embed = None
                do_video_upload = True
        elif request_info == "link":
            if submission.submission_type.is_self():
                raise CommandUseFailure("Post must be a link post")
            content = submission.url
        elif request_info == "url":
            content = f"https://www.reddit.com{submission.permalink}"
        elif request_info == "shortlink":
            content = submission.shortlink
        elif request_info == "gallery":
            if submission.submission_type is not SubmissionType.GALLERY:
                raise CommandUseFailure("Post must be a gallery post")
            content = request_info_gallery(self.bot.reddit, submission)
        elif request_info == "poll":
            if submission.submission_type is not SubmissionType.POLL:
                raise CommandUseFailure("Post must be a poll post")
            content = request_info_poll(self.bot.reddit, submission)
        else:
            raise CommandUseFailure("Invalid request_info string")

        message: SlashMessage = await ctx.send(content=content, embed=embed, embeds=embeds, hidden=hidden)

        if do_video_upload:
            upload_message = await ctx.send("Attempting video upload...")
            async def on_video_success(file):
                await message.edit(content=message.content, embed=message.embeds[0])
                await upload_message.edit(file=discord.File(fp=file))
                await upload_message.edit(content=None)
            async def on_video_failure():
                await upload_message.delete()
            await do_reddit_video_download(self.bot, submission, on_video_success, on_video_failure)
