from poloniex.app import SyncApp

__author__ = 'andrew.shvv@gmail.com'

API_KEY = "YOUR_API_KEY"
API_SECRET = "YOUR_API_SECRET"

app = SyncApp(api_key=API_KEY, api_sec=API_SECRET)
app.logger.debug(app.public.return24hVolume())
