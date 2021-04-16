from discord.ext import commands


class MyCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
