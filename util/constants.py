from dataclasses import dataclass


@dataclass
class DiscordLimit:
    file_limit: int = 8000000


@dataclass
class EmbedLimit:
    title: int = 256
    description: int = 2048
    fields: int = 25
    field_name: int = 256
    field_value: int = 1024
    footer_text: int = 2048
    author_name: int = 256


PUA = "\uE000"
"""Unicode Private Use Area start"""
