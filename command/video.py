import asyncio
import os

import discord
import requests
import youtube_dl as youtube_dl
from asyncpraw import Reddit
from asyncpraw.models import Submission
from discord_slash import SlashContext
from discord_slash.model import SlashMessage

from util import DiscordLimit


# noinspection PyMethodMayBeStatic
class YdlLogger(object):
    def debug(self, msg):
        pass

    def warning(self, msg):
        pass

    def error(self, msg):
        print(msg)


def get_reddit_video_approx_size(reddit: Reddit, submission: Submission):
    response = requests.head(submission.media["reddit_video"]["fallback_url"])
    return int(response.headers["Content-Length"])


async def do_reddit_video_upload(bot, ctx: SlashContext, submission_message: SlashMessage,
                                 submission: Submission):
    if get_reddit_video_approx_size(bot.reddit, submission) > DiscordLimit.file_limit:
        return
    upload_message = await ctx.send("Attempting video upload...")
    async with bot.video_lock:
        filename = f"@videos/{submission.id}.mp4"
        with youtube_dl.YoutubeDL({
            "logger": YdlLogger(),
            "outtmpl": filename,
        }) as ydl:
            ydl.download([submission.url])
        with open(filename, "rb") as file:
            if os.path.getsize(file.name) > DiscordLimit.file_limit:
                await upload_message.delete()
            else:
                await submission_message.edit(content=submission_message.content, embed=submission_message.embeds[0])
                await upload_message.edit(file=discord.File(fp=file))
                await upload_message.edit(content=None)
        os.remove(filename)
