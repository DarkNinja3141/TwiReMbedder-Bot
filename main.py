from dataclasses import asdict
import signal
import time

from discord import Status, Activity, ActivityType
from discord.ext.commands import Bot, Context
from discord_slash import SlashCommand
import asyncpraw

from component import cogs
from config import config, Config


class MyBot(Bot):
    def __init__(self, config_: Config):
        self.config: Config = config_
        super().__init__(command_prefix=self.config.prefix, owner_id=self.config.owner, status=Status.online)
        self.reddit = asyncpraw.Reddit(**asdict(self.config.reddit))
        self.loop.create_task(self.startup())
        self.remove_command("help")  # Remove help command

    def add_cogs(self):
        for cog in cogs:
            self.add_cog(cog(self))

    async def on_command_error(self, ctx: Context, exception):
        pass

    def _signal(self):
        try:
            self.loop.remove_signal_handler(signal.SIGTERM)
            self.loop.add_signal_handler(signal.SIGTERM, lambda: self.loop.create_task(self.terminate()))
        except NotImplementedError:
            pass

    async def startup(self):
        await self.wait_until_ready()
        self._signal()
        await self.change_presence(activity=Activity(type=ActivityType.watching, name="trm.help"))
        print('Logged in as')
        print(self.user.name)
        print(self.user.id)
        print("/u/" + (await self.reddit.user.me()).name)
        print('------')

    async def terminate(self):
        try:
            await self.change_presence(status=Status.offline)
        finally:
            await self.close()
            time.sleep(1)


client: MyBot = MyBot(config)
slash = SlashCommand(client, sync_commands=True)
client.add_cogs()


if __name__ == "__main__":
    client.run(config.token)
