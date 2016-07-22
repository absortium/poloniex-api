import asyncio
import signal
import sys

import aiohttp

from poloniex.api import async, sync
from poloniex.error import PoloniexError
from poloniex.logger import getLogger

__author__ = 'andrew.shvv@gmail.com'


class Application:
    def __init__(self, api_key=None, api_sec=None):
        super().__init__()
        self.api_key = api_key
        self.api_sec = api_sec
        self.logger = getLogger(__name__)

        self._trading = None
        self.public = None
        self.push = None

    @property
    def trading(self):
        if not self._trading:
            raise PoloniexError('In order to be able to use trading api you need provide API and SEC keys')
        return self._trading


class SyncApp(Application):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.init_api()

    def init_api(self):
        self.public = sync.PublicApi()

        if self.api_key and self.api_sec:
            self._trading = sync.TradingApi(api_key=self.api_key, api_sec=self.api_sec)


class AsyncApp(Application):
    def init_api(self, loop=None, session=None):
        def stop_handler(*args, **kwargs):
            self.stop()
            sys.exit(0)

        signal.signal(signal.SIGINT, stop_handler)

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

    def stop(self):
        self.loop.call_soon_threadsafe(self.loop.stop)

    def run(self, session=None):
        self.loop = asyncio.get_event_loop()

        if not session:
            with aiohttp.ClientSession(loop=self.loop) as session:
                self.init_api(self.loop, session)
        else:
            self.init_api(self.loop, session)

    async def main(self):
        raise NotImplementedError("method 'main' should be overridden!")
