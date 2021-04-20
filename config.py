import json
import re
from typing import Any, Dict, List

import yaml
from dataclasses import dataclass, field
import dacite


@dataclass
class Versions:
    """Bot and library versions"""
    version: str
    python: str
    discord_py: str
    discord_py_slash_command: str
    dacite: str
    asyncpraw: str
    pyyaml: str


@dataclass
class Reddit:
    """Reddit API credentials"""
    client_id: str
    client_secret: str
    user_agent: str
    username: str
    password: str


@dataclass()
class Debug:
    """Debug settings"""
    enabled: bool
    guild_ids: List[int] = field(default_factory=list)


@dataclass
class Config:
    """Bot settings and credentials"""
    token: str
    prefix: str
    owner: int
    reddit: Reddit
    debug: Debug = Debug(enabled=False)


def escape_keys(dct: Dict[str, Any]):
    if not isinstance(dct, Dict):
        return dct
    return {re.sub(r'\W', "_", k, re.ASCII): escape_keys(v) for k, v in dct.items()}


with open("versions.yaml", "r") as versions_yaml:
    versions: Versions = dacite.from_dict(Versions, escape_keys(yaml.safe_load(versions_yaml)))

with open("config.json", "r") as config_json:
    config: Config = dacite.from_dict(Config, json.load(config_json))
config.reddit.user_agent = config.reddit.user_agent.format(version=versions.version)
