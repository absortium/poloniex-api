__author__ = 'andrey.samokhvalov21@yandex.ru'

import asyncio

import aiohttp
from pprintpp import pprint as print

from poloniex.api import TradingApi, PublicApi, PushApi

API_KEY = "PCCD7XFZ-FMFB8UOT-SAUH774K-IHNW7M2N"
API_SECRET = "7088d5ecdc029593aec888481d68f4d07ac061a817970d127962f00424a8860fac41b3db1e163462b56aa7a175d7484714e33db349a6829c9ae472a7098788ea"


class Poloniex():
    def __init__(self, API_KEY=None, SEC_KEY=None):
        self.public_api = PublicApi()
        self.push_api = PushApi()

        self._trading_api = None
        if (API_KEY is not None) and (SEC_KEY is not None):
            self._trading_api = TradingApi(API_KEY, SEC_KEY)

    @property
    def trading_api(self):
        if self._trading_api is None:
            raise Exception('In order to be able to use trading api you need provide API and SEC keys')
        return self._trading_api

    async def main(self, client):
        pass

    def run(self):
        loop = asyncio.get_event_loop()

        with aiohttp.ClientSession(loop=loop) as client:
            if self.push_api.hasSubscriptions:
                g = asyncio.gather(self.push_api.start(client), self.main(client))
                loop.run_until_complete(g)

def trollbox_handler(msg):
    print(msg)


async def public_api_main(client):
    public_api = PublicApi(client)
    r = await public_api.return24Volume()
    print(r)


async def push_api_main(client):
    push_api = PushApi(client)
    # trading_api = TradingApi(client, API_KEY, API_SECRET)
    push_api.trollbox(trollbox_handler)
    await push_api.start()
