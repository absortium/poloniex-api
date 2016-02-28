__author__ = 'andrew.shvv@gmail.com'

from logging import DEBUG
from poloniex.app import Application

API_KEY = "YOUR_API_KEY"
API_SECRET = "YOUR_API_SECRET"


class App(Application):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger.setLevel(DEBUG)

    async def ticker(self, **kwargs):
        self.logger.info(kwargs)

    async def trades(self, **kwargs):
        self.logger.info(kwargs)

    async def main(self):
        await self.push_api.subscribe(topic="BTC_ETH", handler=self.trades)
        await self.push_api.subscribe(topic="ticker", handler=self.ticker)
        volume = await self.public_api.return24Volume()

        self.logger.info(volume)


app = App(api_key=API_KEY, api_sec=API_SECRET)
app.run()
