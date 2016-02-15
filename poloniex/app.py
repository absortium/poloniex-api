__author__ = 'andrew.shvv@gmail.com'

import asyncio

import aiohttp

from poloniex.api import TradingApi, PublicApi, PushApi


class Application():
    def __init__(self, api_key=None, api_sec=None):
        self.api_key = api_key
        self.api_sec = api_sec

    @property
    def trading_api(self):
        if self._trading_api is None:
            raise Exception('In order to be able to use trading api you need provide API and SEC keys')
        return self._trading_api

    async def main(self):
        pass

    def run(self):
        loop = asyncio.get_event_loop()

        with aiohttp.ClientSession(loop=loop) as client:
            self.public_api = PublicApi(client=client)
            self.push_api = PushApi(client=client)
            self._trading_api = None

            if (self.api_key is not None) and (self.api_sec is not None):
                self._trading_api = TradingApi(api_key=self.api_key, api_sec=self.api_sec, client=client)

                application = self
                g = asyncio.gather(self.push_api.start(application), self.main())
                loop.run_until_complete(g)
