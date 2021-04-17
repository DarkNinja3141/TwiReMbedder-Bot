import json
from dataclasses import dataclass
import dacite


@dataclass
class Reddit:
    """Reddit API credentials"""
    client_id: str
    client_secret: str
    user_agent: str
    username: str
    password: str


@dataclass
class Config:
    """Bot settings and credentials"""
    token: str
    prefix: str
    owner: int
    reddit: Reddit


with open("config.json", "r") as config_json:
    config: Config = dacite.from_dict(Config, json.load(config_json))
