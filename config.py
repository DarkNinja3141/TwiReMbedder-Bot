import json
from dataclasses import dataclass


@dataclass
class Config:
    token: str
    prefix: str
    owner: int


with open("config.json", "r") as config_json:
    config: Config = json.load(config_json, object_hook=(lambda dct: Config(**dct)))
