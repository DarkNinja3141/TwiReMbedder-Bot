import datetime
from enum import Enum, auto
from typing import Tuple, Union, List
from urllib.parse import urlparse

from asyncpraw import Reddit
from asyncpraw.models import Submission, Redditor, PollData, PollOption
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
        if submission_type.is_self()
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


async def get_reddit_poll_embed(reddit: Reddit, submission: Submission) -> Union[Embed, None]:
    if SubmissionType.get_submission_type(submission) is not SubmissionType.POLL:
        return None
    poll_data: PollData = submission.poll_data
    total_vote_count: int
    voting_end_timestamp: float
    options: List[PollOption]
    # noinspection PyUnresolvedReferences
    total_vote_count, voting_end_timestamp, options = (poll_data.total_vote_count,
                                                       poll_data.voting_end_timestamp / 1000.0,
                                                       poll_data.options)

    voting_end = datetime.datetime.fromtimestamp(voting_end_timestamp, datetime.timezone.utc)
    poll_active: bool = datetime.datetime.now(datetime.timezone.utc) < voting_end
    embed: Embed = Embed(
        title=submission.title[:EmbedLimit.title],
        url=f"https://www.reddit.com/poll/{submission.id}",
        description="Poll is active. No results." if poll_active else EmptyEmbed,
        color=Color.from_rgb(255, 69, 0),
        timestamp=voting_end,
    ).set_author(
        name=f"{total_vote_count:,} vote{'' if total_vote_count == 1 else 's'}"
             f": Poll {'active' if poll_active else 'closed'}",
    ).set_footer(text="Voting ends at")

    if poll_active:
        return embed

    poll_option_bar_fill = ["\U0001F7E5", "\U0001F7E6", "\U0001F7E9", "\U0001F7E8", "\U0001F7EA", "\U0001F7E7"]
    for i in range(len(options)):
        option: PollOption = options[i]
        vote_count: int
        text: str
        # noinspection PyUnresolvedReferences
        vote_count, text = (option.vote_count, option.text)
        percentage: int = round(float(vote_count)/float(total_vote_count) * 100.0) if total_vote_count != 0 else 0
        option_bar = get_poll_option_bar(percentage, poll_option_bar_fill[i], "\u2B1B")
        embed.add_field(name=text,
                        value=f"{option_bar} {vote_count:,} vote{'' if vote_count == 1 else 's'} ({percentage}%)",
                        inline=False)

    return embed


def get_poll_option_bar(percentage: int, bar_left: str, bar_right: str) -> str:
    num_left = int(round(percentage, -1) / 10)  # Round to nearest 10 and divide by 10
    num_right = 10 - num_left
    return (str(bar_left) * num_left) + (str(bar_right) * num_right)


async def get_reddit_gallery_embed(reddit: Reddit, submission: Submission) -> Union[Embed, None]:
    if SubmissionType.get_submission_type(submission) is not SubmissionType.GALLERY:
        return None
    gallery_data = submission.gallery_data
    media_metadata = submission.media_metadata
    embed: Embed = Embed(
        title="Image Gallery",
        url=f"https://www.reddit.com/gallery/{submission.id}",
        color=Color.from_rgb(255, 69, 0),
    )
    digits = [
        "One", "Two", "Three", "Four", "Five",
        "Six", "Seven", "Eight", "Nine", "Ten",
        "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen",
        "Sixteen", "Seventeen", "Eighteen", "Nineteen", "Twenty"
    ]

    def image_link(i: int) -> str:
        # Get text for link
        return f"[{digits[min(i, 19)]}]" \
               f"(https://i.redd.it{urlparse(media_metadata[gallery_data['items'][i]['media_id']]['s']['u']).path})"
        # Get media id from gallery_data, then dig into media_metadata[id], then extract the id.png part of the url

    # Use this to test emojis for a gallery of 21 images
    # for i in range(len(gallery_data['items']), 21):
    #     gallery_data['items'].append(gallery_data['items'][len(gallery_data['items'])-1])
    links: List[str] = list(map(image_link, range(0, len(gallery_data['items']))))
    links_row_1 = " ".join(links[0:5])
    links_row_2 = " ".join(links[5:10])
    links_row_3 = " ".join(links[10:15])
    links_row_4 = " ".join(links[15:])

    embed.description = f"Click an emoji to view an image\n\n" \
                        + "\n".join([links_row_1, links_row_2, links_row_3, links_row_4])
    return embed
