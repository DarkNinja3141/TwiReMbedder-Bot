from dataclasses import dataclass


@dataclass
class CommandUseFailure(Exception):
    message: str
