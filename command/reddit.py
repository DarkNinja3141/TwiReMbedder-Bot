import datetime
from enum import Enum, auto
from typing import Tuple

from asyncpraw import Reddit
from asyncpraw.models import Submission, Redditor
from discord import Embed, Color
from discord.embeds import EmptyEmbed

from util import EmbedLimit


class SubmissionType(Enum):
    SELF = auto()
    POLL = auto()
    LINK = auto()
    IMAGE = auto()
    VIDEO = auto()
    GALLERY = auto()

    @classmethod
    def get_submission_type(cls, submission: Submission):
        if submission.is_self:
            if hasattr(submission, "poll_data"):
                return cls.POLL
            return cls.SELF
        else:
            if hasattr(submission, "post_hint") and submission.post_hint == "image":
                return cls.IMAGE
            elif hasattr(submission, "post_hint") and submission.post_hint == "hosted:video":
                return cls.VIDEO
            elif hasattr(submission, "is_gallery") and submission.is_gallery is True:
                return cls.GALLERY
            return cls.LINK

    @classmethod
    def type_is_self(cls, submission_type: "SubmissionType"):
        return submission_type is cls.SELF or submission_type is cls.POLL

    def is_self(self):
        return SubmissionType.type_is_self(self)


async def get_reddit_embed(reddit: Reddit, submission: Submission) -> Tuple[str, Embed]:
    """
    Takes a reddit url and turns it into a discord embed

    :raises util.error.CommandUseFailure
    """
    submission_type: SubmissionType = SubmissionType.get_submission_type(submission)
    author: Redditor = await reddit.redditor(name=submission.author, fetch=True)
    safe_url = f"https://www.reddit.com{submission.permalink}"

    content = f"<{safe_url}>"
    embed: Embed = Embed(
        title=submission.title[:EmbedLimit.title],
        url=safe_url,
        description=submission.selftext[:EmbedLimit.description]
        if submission_type == SubmissionType.SELF
        else EmptyEmbed,
        color=Color.from_rgb(255, 69, 0),
        timestamp=datetime.datetime.utcfromtimestamp(submission.created_utc),
    ).set_author(
        name=f"/u/{author.name}",
        url=f"https://www.reddit.com/u/{author.name}",
        icon_url=author.icon_img if hasattr(author, "icon_img") else EmptyEmbed
    ).add_field(
        name="Score",
        value=f"{submission.score:,}",
        inline=True,
    ).add_field(
        name="Comments",
        value=f"{submission.num_comments:,}",
        inline=True,
    ).set_footer(
        text=f"Reddit - /r/{submission.subreddit}",
        icon_url="https://www.redditstatic.com/desktop2x/img/favicon/favicon-96x96.png",
    ).set_thumbnail(
        url=submission.thumbnail
        if hasattr(submission, "thumbnail")
        and submission_type is not SubmissionType.IMAGE
        and not submission_type.is_self()
        else EmptyEmbed
    ).set_image(
        url=submission.url if submission_type is SubmissionType.IMAGE else EmptyEmbed
    )

    return content, embed
