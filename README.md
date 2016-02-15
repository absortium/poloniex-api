```python
from poloniex.api import subscribe
from poloniex.app import Application

API_KEY = "YOUR_API_KEY"
API_SECRET = "YOUR_API_SEC"

class App(Application):
    @subscribe('trollbox')
    def trollbox(self, msg):
        print(msg)

    @subscribe('ticker')
    def ticker(self, msg):
        print(msg)

    async def main(self):
        r = await self.public_api.return24Volume()
        print(r)
        r = await self.public_api.return24Volume()
        print(r)
        r = await self.public_api.return24Volume()
        print(r)

app = App(api_key=API_KEY, api_sec=API_SECRET)
app.run()
```
