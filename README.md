## Async Example
```python
from poloniex.app import AsyncApp

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

```

## Sync Example
```python
from poloniex.app import SyncApp

API_KEY = "YOUR_API_KEY"
API_SECRET = "YOUR_API_SECRET"

app = SyncApp(api_key=API_KEY, api_sec=API_SECRET)
app.logger.debug(app.public.return24hVolume())
```
