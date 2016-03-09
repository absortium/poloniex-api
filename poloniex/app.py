import asyncio

import aiohttp

from .api import TradingApi, PublicApi, PushApi
from .logger import LogMixin

__author__ = 'andrew.shvv@gmail.com'


class Application(LogMixin):
    def __init__(self, api_key=None, api_sec=None):
        super().__init__()
        self.api_key = api_key
        self.api_sec = api_sec

    @property
    def trading_api(self):
        if not hasattr(self, '_trading_api'):
            raise Exception('In order to be able to use trading api you need provide API and SEC keys')
        return self._trading_api

    async def main(self):
        raise NotImplementedError("method 'main' should be overriden!")

    async def _main(self):
        await self.main()

        # after the 'main' function execution we should check - are there any subscription
        # if not than stop execution
        [waiting, registred] = self.push_api.subsciptions
        if len(waiting)+len(registred) == 0:
            await self.push_api.stop()

    def _start(self, loop, session):
        self.public_api = PublicApi(session=session)
        self.push_api = PushApi(session=session)

        if (self.api_key is not None) and (self.api_sec is not None):
            self._trading_api = TradingApi(api_key=self.api_key, api_sec=self.api_sec, session=session)

        g = asyncio.gather(self.push_api.start(), self._main())
        loop.run_until_complete(g)

    def run(self, session=None):
        loop = asyncio.get_event_loop()
        if session is None:
            with aiohttp.ClientSession(loop=loop) as session:
                self._start(loop, session)
        else:
            self._start(loop, session)
