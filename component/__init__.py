from typing import List, Type

from .MyCog import MyCog
from .RedditSlashCommands import RedditSlashCommands

cogs: List[Type[MyCog]] = [RedditSlashCommands]
