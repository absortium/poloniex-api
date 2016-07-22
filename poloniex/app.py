import asyncio

import aiohttp

from poloniex.api import async, sync
from poloniex.logger import getLogger

__author__ = 'andrew.shvv@gmail.com'


class Application:
    def __init__(self, api_key=None, api_sec=None, async=True):
        super().__init__()
        self.api_key = api_key
        self.api_sec = api_sec
        self.logger = getLogger(__name__)

        if not async:
            self.init_sync_api()

    @property
    def trading_api(self):
        if not hasattr(self, '_trading_api'):
            raise Exception('In order to be able to use trading api you need provide API and SEC keys')
        return self._trading_api

    async def main(self):
        raise NotImplementedError("method 'main' should be overridden!")

    def init_async_api(self, loop=None, session=None):
        self.public_api = async.PublicApi(session=session)
        self.push_api = async.PushApi(session=session)

        if self.api_key and self.api_sec:
            self._trading_api = async.TradingApi(api_key=self.api_key, api_sec=self.api_sec, session=session)

        def stop_decorator(main, api):
            async def decorator(*args, **kwargs):
                await main(*args, **kwargs)
                await api.stop(force=False)

            return decorator

        g = asyncio.gather(
            self.push_api.wamp.start(),
            stop_decorator(self.main, self.push_api)()
        )

        loop.run_until_complete(g)

    def init_sync_api(self):
        self.public_api = sync.PublicApi()

        if self.api_key and self.api_sec:
            self._trading_api = sync.TradingApi(api_key=self.api_key, api_sec=self.api_sec)

    def run(self, session=None):
        loop = asyncio.get_event_loop()

        if not session:
            with aiohttp.ClientSession(loop=loop) as session:
                self.init_async_api(loop, session)
        else:
            self.init_async_api(loop, session)
