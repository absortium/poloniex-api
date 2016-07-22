import asyncio

import aiohttp

from poloniex.api import async, sync
from poloniex.error import PoloniexError
from poloniex.logger import getLogger

__author__ = 'andrew.shvv@gmail.com'


class Application:
    def __init__(self, api_key=None, api_sec=None, async=True):
        super().__init__()
        self.api_key = api_key
        self.api_sec = api_sec
        self.logger = getLogger(__name__)
        self.async = async

        if not async:
            self.init_sync_api()

    @property
    def trading(self):
        if not hasattr(self, '_trading'):
            raise Exception('In order to be able to use trading api you need provide API and SEC keys')
        return self._trading

    def init_async_api(self, loop=None, session=None):
        self.public = async.PublicApi(session=session)
        self.push = async.PushApi(session=session)

        if self.api_key and self.api_sec:
            self._trading = async.TradingApi(api_key=self.api_key, api_sec=self.api_sec, session=session)

        def stop_decorator(main, api):
            async def decorator(*args, **kwargs):
                await main(*args, **kwargs)
                await api.stop(force=False)

            return decorator

        g = asyncio.gather(
            self.push.wamp.start(),
            stop_decorator(self.main, self.push)()
        )

        loop.run_until_complete(g)

    def init_sync_api(self):
        self.public = sync.PublicApi()

        if self.api_key and self.api_sec:
            self._trading = sync.TradingApi(api_key=self.api_key, api_sec=self.api_sec)

    def run(self, session=None):
        if self.async:
            loop = asyncio.get_event_loop()

            if not session:
                with aiohttp.ClientSession(loop=loop) as session:
                    self.init_async_api(loop, session)
            else:
                self.init_async_api(loop, session)
        else:
            raise PoloniexError("'run' function is used for async api.")

    async def main(self):
        raise NotImplementedError("method 'main' should be overridden!")
