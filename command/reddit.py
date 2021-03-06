import datetime
from enum import Enum, auto
from typing import Tuple, Union, List
from urllib.parse import urlparse

from asyncpraw import Reddit
from asyncpraw.models import Submission, Redditor, PollData, PollOption
from asyncpraw.reddit import Comment
from discord import Embed, Color
from discord.embeds import EmptyEmbed

from util import *


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
    submission_type: SubmissionType = submission.submission_type
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
        and submission.thumbnail != "default"
        and submission_type is not SubmissionType.IMAGE
        and submission_type is not SubmissionType.VIDEO
        and not submission_type.is_self()
        else EmptyEmbed
    ).set_image(
        url=submission.url if submission_type is SubmissionType.IMAGE else EmptyEmbed
    )
    awards = get_reddit_awards(submission)
    if awards:
        embed.add_field(
            name="Awards",
            value=awards,
            inline=True,
        )

    return content, embed


async def get_reddit_comment_embed(reddit: Reddit, comment: Comment) -> Tuple[str, Embed]:
    """Takes a reddit comment url and turns it into a discord embed"""
    author: Redditor = await reddit.redditor(name=comment.author.name, fetch=True)
    safe_url = f"https://www.reddit.com{comment.permalink}"

    content = f"<{safe_url}>"
    embed: Embed = Embed(
        title="Comment on a user's submission" if comment.is_root else "Reply to another user's comment",
        url=safe_url,
        description=comment.body,
        color=Color.from_rgb(255, 69, 0),
        timestamp=datetime.datetime.utcfromtimestamp(comment.created_utc),
    ).set_author(
        name=f"/u/{author.name}",
        url=f"https://www.reddit.com/u/{author.name}",
        icon_url=author.icon_img if hasattr(author, "icon_img") else EmptyEmbed
    ).add_field(
        name="Score",
        value=f"{comment.score:,}",
        inline=True,
    ).add_field(
        name="Replies",
        value=f"{len(comment.replies):,}",
        inline=True,
    ).set_footer(
        text=f"Reddit - /r/{comment.subreddit}",
        icon_url="https://www.redditstatic.com/desktop2x/img/favicon/favicon-96x96.png",
    )
    awards = get_reddit_awards(comment)
    if awards:
        embed.add_field(
            name="Awards",
            value=awards,
            inline=True,
        )

    return content, embed


BRONZE_RANGE = interval(None, 100, incl_end=False)
SILVER_RANGE = interval(100, 500, incl_end=False)
GOLD_RANGE = interval(500, 1800, incl_end=False)
PLATINUM_RANGE = interval(1800, None)


def get_reddit_awards(submission: Union[Submission, Comment]) -> str:
    awards = [0, 0, 0, 0]  # platinum, gold, silver, bronze
    for award in submission.all_awardings:
        for award_index, award_type in enumerate((PLATINUM_RANGE, GOLD_RANGE, SILVER_RANGE, BRONZE_RANGE)):
            if award["coin_price"] in award_type:
                awards[award_index] += award["count"]
                break
    return "".join(
        f"{emoji}{awards[award_index]:,}"
        for award_index, emoji in enumerate((":medal:", ":first_place:", ":second_place:", ":third_place:"))
        if awards[award_index] > 0
    )


async def get_reddit_poll_embed(reddit: Reddit, submission: Submission) -> Union[Embed, None]:
    if submission.submission_type is not SubmissionType.POLL:
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
    if submission.submission_type is not SubmissionType.GALLERY:
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

    embed.description = f"Click a word to view an image\n\n" \
                        + "\n".join([links_row_1, links_row_2, links_row_3, links_row_4])
    return embed


async def get_reddit_video_embed(reddit: Reddit, submission: Submission) -> Union[Embed, None]:
    if submission.submission_type is not SubmissionType.VIDEO:
        return None
    duration = submission.media["reddit_video"]["duration"]
    hours, remainder = divmod(duration, 3600)
    minutes, seconds = divmod(remainder, 60)
    embed: Embed = Embed(
        title="Reddit Video",
        url=submission.url,
        color=Color.from_rgb(255, 69, 0),
    ).add_field(
        name="Duration",
        value=(
                  f"{hours}:{minutes:02}" if hours >= 1 else f"{minutes}"
              ) + f":{seconds:02}"
    ).set_thumbnail(
        url=submission.thumbnail
        if hasattr(submission, "thumbnail")
        and submission.thumbnail != "default"
        else EmptyEmbed
    )
    return embed


def request_info_gallery(reddit: Reddit, submission: Submission) -> Union[str, None]:
    if submission.submission_type is not SubmissionType.GALLERY:
        return None
    gallery_data = submission.gallery_data
    media_metadata = submission.media_metadata

    def image_link(i: int) -> str:
        num = i+1
        return f"**{num}**\n" \
               f"https://i.redd.it{urlparse(media_metadata[gallery_data['items'][i]['media_id']]['s']['u']).path}"

    return "\n".join(map(image_link, range(0, len(gallery_data['items']))))


def request_info_poll(reddit: Reddit, submission: Submission) -> Union[str, None]:
    if submission.submission_type is not SubmissionType.POLL:
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

    if poll_active:
        return "Poll is active. No results."

    options_texts: List[str] = []
    poll_option_bar_fill = ["\U0001F7E5", "\U0001F7E6", "\U0001F7E9", "\U0001F7E8", "\U0001F7EA", "\U0001F7E7"]
    for i in range(len(options)):
        option: PollOption = options[i]
        vote_count: int
        text: str
        # noinspection PyUnresolvedReferences
        vote_count, text = (option.vote_count, option.text)
        percentage: int = round(float(vote_count) / float(total_vote_count) * 100.0) if total_vote_count != 0 else 0
        option_bar = get_poll_option_bar(percentage, poll_option_bar_fill[i], "\u2B1B")
        options_texts.append(
            f"**{text}**\n"
            f"{option_bar} {vote_count:,} vote{'' if vote_count == 1 else 's'} ({percentage}%)"
        )

    return "\n".join(options_texts)
