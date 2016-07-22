from poloniex.app import AsyncApp

__author__ = 'andrew.shvv@gmail.com'

API_KEY = "YOUR_API_KEY"
API_SECRET = "YOUR_API_SECRET"


class App(AsyncApp):
    def ticker(self, **kwargs):
        self.logger.info(kwargs)

    def trades(self, **kwargs):
        self.logger.info(kwargs)

    async def main(self):
        self.push.subscribe(topic="BTC_ETH", handler=self.trades)
        self.push.subscribe(topic="ticker", handler=self.ticker)
        volume = await self.public.return24hVolume()

        self.logger.info(volume)


app = App(api_key=API_KEY, api_sec=API_SECRET)
app.run()
