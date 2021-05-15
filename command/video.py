import asyncio
import os
import re
from typing import Tuple, List, Callable, BinaryIO, Awaitable
import xml.etree.ElementTree as xml_ET
from urllib.parse import urljoin, urlparse

import aiofiles
import aiohttp
import ffmpeg
from aiohttp import ClientSession
from asyncpraw.models import Submission

from util import DiscordLimit, find, remove_file


def get_urls_from_mpd(base_url: str, mpd_body: str) -> Tuple[str, List[str]]:
    mpd: xml_ET.ElementTree = xml_ET.ElementTree(xml_ET.fromstring(mpd_body))
    namespaces = {'': re.search("{(.*)}", mpd.getroot().tag)[1]}
    reps = mpd.findall(".//Representation", namespaces)
    try:
        audio_path = find(reps, lambda e: e.get("id").lower().startswith("audio")).find("BaseURL", namespaces).text
    except AttributeError:  # If there is no audio
        audio_path = None
    audio = urljoin(base_url, audio_path) if audio_path else None
    videos = [
        urljoin(base_url, e.find("BaseURL", namespaces).text)
        for e in sorted(reps, key=lambda x: int(x.get("bandwidth")), reverse=True)
        if e.get("id").lower().startswith("video")
    ]
    return audio, videos


async def get_video_approx_size(session: ClientSession, url: str):
    try:
        async with session.head(url) as response:
            return int(response.headers["Content-Length"])
    except:
        return 0


async def do_reddit_video_download(bot, submission: Submission,
                                   on_success: Callable[[BinaryIO], Awaitable[None]],
                                   on_failure: Callable[[], Awaitable[None]]):
    # noinspection PyProtectedMember
    headers = {
        "User-Agent": bot.config.user_agent,
        "Authorization": f"Bearer {bot.reddit._core._authorizer.access_token}",
    }
    async with aiohttp.ClientSession(headers=headers) as session:
        mpd_url = submission.media["reddit_video"]["dash_url"]
        async with session.get(mpd_url) as r:
            mpd_body = await r.text()
        audio_url, video_urls = get_urls_from_mpd(mpd_url, mpd_body)
        # noinspection PyProtectedMember
        fallback_url = urlparse(submission.media["reddit_video"]["fallback_url"])._replace(query=None).geturl()
        if fallback_url != video_urls[0]:
            video_urls.insert(0, fallback_url)
        for video_url in video_urls:
            if await get_video_approx_size(session, video_url) > DiscordLimit.file_limit:
                continue
            try:
                audio_filename = f"@videos/audio_{submission.id}.mp4"
                video_filename = f"@videos/video_{submission.id}.mp4"
                filename = f"@videos/{submission.id}.mp4"
                async def get_audio():
                    async with session.get(audio_url) as resp:
                        async for data in resp.content.iter_any():
                            async with aiofiles.open(audio_filename, "ba") as f:
                                await f.write(data)
                async def get_video():
                    async with session.get(video_url) as resp:
                        async for data in resp.content.iter_any():
                            async with aiofiles.open(video_filename, "ba") as f:
                                await f.write(data)
                if audio_url:
                    await asyncio.gather(get_audio(), get_video())
                else:
                    await get_video()
                async def run_ffmpeg():
                    inputs = [ffmpeg.input(video_filename), ffmpeg.input(audio_filename)] \
                             if audio_url else [ffmpeg.input(video_filename)]
                    ffmpeg.output(
                        *inputs,
                        filename,
                        strict="-2",
                        loglevel="quiet",
                    ).run()
                await run_ffmpeg()

                with open(filename, "rb") as file:
                    if os.path.getsize(file.name) <= DiscordLimit.file_limit:
                        await on_success(file)
                        return
            finally:
                remove_file(audio_filename)
                remove_file(video_filename)
                remove_file(filename)
    await on_failure()
