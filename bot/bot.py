import asyncio
import logging
import socket

import aiohttp
from discord.ext.commands import Bot, CommandError, Context

from .disable import DisableApi
from .graphql import GraphQLClient
from .settings import API_COGS

log = logging.getLogger(__name__)


class Friendo(Bot):
    """Base Class for the discord bot."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        # Setting the loop.
        self.loop = asyncio.get_event_loop()

        self._resolver = aiohttp.AsyncResolver()
        self._connector = aiohttp.TCPConnector(
            resolver=self._resolver,
            family=socket.AF_INET,
        )
        # Client.login() will call HTTPClient.static_login() which will create a session using
        # this connector attribute.
        self.http.connector = self._connector

        self.session = aiohttp.ClientSession(connector=self._connector)
        self.graphql = GraphQLClient(connector=self._connector)

    @staticmethod
    async def on_ready() -> None:
        """Runs when the bot is connected."""
        log.info('Awaiting...')
        log.info("Bot Is Ready For Commands")

    async def on_command_error(self, ctx: Context, exception: CommandError) -> None:
        """Fired when exception happens."""
        log.error(
            "Exception happened while executing command",
            exc_info=(type(exception), exception, exception.__traceback__)
        )

    async def close(self) -> None:
        """Make sure connections are closed properly."""
        await super().logout()

        if self.graphql:
            await self.graphql.close()

        if self.session:
            await self.session.close()

        if self._connector:
            await self._connector.close()

        if self._resolver:
            await self._resolver.close()

    def load_extension(self, name: str) -> None:
        """Loads an extension after checking if it's disabled or not."""
        disable_api = DisableApi()
        cog_name = name.split(".")[-1]

        # If no-api is passed disable API_COGS ie. memes and events
        if disable_api.get_no_api() and cog_name in API_COGS:
            return

        disabled_list = disable_api.get_disable()

        if disabled_list:
            if cog_name in disabled_list:
                return

            # If cog is not disabled, load it
            else:
                super().load_extension(name)
                return

        enabled_list = disable_api.get_enable()

        if enabled_list:
            # If cog is enabled, load it
            if cog_name in enabled_list:
                super().load_extension(name)
                return

            # Don't load cogs not passed along with enable
            else:
                return

        # load cogs if no argument is passed
        super().load_extension(name)
