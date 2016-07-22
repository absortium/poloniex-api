from poloniex.app import Application as App

__author__ = 'andrew.shvv@gmail.com'

API_KEY = "YOUR_API_KEY"
API_SECRET = "YOUR_API_SECRET"

app = App(api_key=API_KEY, api_sec=API_SECRET, async=False)
app.logger.debug(app.public.return24hVolume())
