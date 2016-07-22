import inspect
from datetime import datetime, timedelta

from poloniex import constants
from poloniex.api.base import command_operator, BasePublicApi, BaseTradingApi
from poloniex.error import PoloniexError
from poloniex.logger import getLogger
from poloniex.wamp.client import WAMPClient

__author__ = "andrew.shvv@gmail.com"

logger = getLogger(__name__)


def ticker_wrapper(handler):
    async def decorator(data):
        currency_pair = data[0]
        last = data[1]
        lowest_ask = data[2]
        highest_bid = data[3]
        percent_change = data[4]
        base_volume = data[5]
        quote_volume = data[6]
        is_frozen = data[7]
        day_high = data[8]
        day_low = data[9]

        kwargs = {
            "currency_pair": currency_pair,
            "last": last,
            "lowest_ask": lowest_ask,
            "highest_bid": highest_bid,
            "percent_change": percent_change,
            "base_volume": base_volume,
            "quote_volume": quote_volume,
            "is_frozen": is_frozen,
            "day_high": day_high,
            "day_low": day_low
        }

        if inspect.isgeneratorfunction(handler):
            await handler(**kwargs)
        else:
            handler(**kwargs)

    return decorator


def trades_wrapper(topic, handler):
    async def decorator(data):
        for event in data:
            event["currency_pair"] = topic

            if inspect.isgeneratorfunction(handler):
                await handler(**event)
            else:
                handler(**event)

    return decorator


def trollbox_wrapper(handler):
    async def decorator(data):
        if len(data) != 5:
            return

        type_ = data[0]
        message_id = data[1]
        username = data[2]
        text = data[3]
        reputation = data[4]

        kwargs = {
            "id": message_id,
            "username": username,
            "type": type_,
            "text": text,
            "reputation": reputation
        }

        if inspect.isgeneratorfunction(handler):
            await handler(**kwargs)
        else:
            handler(**kwargs)

    return decorator


class PushApi:
    url = "wss://api.poloniex.com"

    def __init__(self, session):
        self.wamp = WAMPClient(url=self.url, session=session)

    async def start(self):
        await self.wamp.start()

    async def stop(self, force=True):
        if force or not self.is_subscribed:
            await self.wamp.stop()

    @property
    def is_subscribed(self):
        [queue, subscriptions] = self.wamp.subsciptions
        return len(queue) + len(subscriptions) != 0

    def subscribe(self, topic, handler):
        if topic in constants.CURRENCY_PAIRS:
            handler = trades_wrapper(topic, handler)
            self.wamp.subscribe(topic=topic, handler=handler)

        elif topic is "trollbox":
            handler = trollbox_wrapper(handler)
            self.wamp.subscribe(topic=topic, handler=handler)

        elif topic is "ticker":
            handler = ticker_wrapper(handler)
            self.wamp.subscribe(topic=topic, handler=handler)

        elif topic in constants.AVAILABLE_SUBSCRIPTIONS:
            self.wamp.subscribe(topic=topic, handler=handler)

        else:
            raise NotImplementedError("Topic not available")


class PublicApi(BasePublicApi):
    def __init__(self, session):
        self.session = session

    async def api_call(self, *args, **kwargs):
        async with self.session.get(self.url, *args, **kwargs) as response:
            logger.debug(response)
            response = await response.json()

            if ("error" in response) and (response["error"] is not None):
                raise PoloniexError(response["error"])

            return response

    @command_operator
    async def returnTicker(self):
        """
        Returns the ticker for all markets
        """
        pass

    @command_operator
    async def return24hVolume(self):
        """
        Returns the 24-hour volume for all markets, plus totals for primary currencies.
        """
        pass

    @command_operator
    async def returnOrderBook(self, currency_pair="all", depth=50):
        """
        Returns the order book for a given market, as well as a sequence number for use with the Push API and an indicator
        specifying whether the market is frozen. You may set currencyPair to "all" to get the order books of all markets
        """
        pass

    @command_operator
    async def returnChartData(self,
                              currency_pair,
                              start=datetime.now() - timedelta(days=1),
                              end=datetime.now(),
                              period=300):
        """
        Returns candlestick chart data. Required GET parameters are "currencyPair", "period" (candlestick period in seconds;
        valid values are 300, 900, 1800, 7200, 14400, and 86400), "start", and "end". "Start" and "end" are given in UNIX
        timestamp format and used to specify the date range for the data returned.
        """
        pass

    @command_operator
    async def returnCurrencies(self):
        """
        Returns information about currencies
        """
        pass

    @command_operator
    async def returnTradeHistory(self,
                                 currency_pair="all",
                                 start=datetime.now() - timedelta(days=1),
                                 end=datetime.now()):
        """
        Returns the past 200 trades for a given market, or up to 50,000 trades between a range specified in UNIX timestamps
        by the "start" and "end" GET parameters.
        """
        pass


class TradingApi(BaseTradingApi):
    def __init__(self, session, *args, **kwargs):
        self.session = session

        super(TradingApi, self).__init__(*args, **kwargs)

    async def api_call(self, *args, **kwargs):
        data, headers = self.secure_request(kwargs.get('data', {}), kwargs.get('headers', {}))

        kwargs['data'] = data
        kwargs['headers'] = headers

        async with self.session.post(self.url, *args, **kwargs) as response:
            return await response.json()

    @command_operator
    async def returnBalances(self):
        """
        Returns all of your available balances
        """
        pass

    @command_operator
    async def returnCompleteBalances(self):
        """
        Returns all of your balances, including available balance, balance on orders, and the estimated BTC value of your balance.
        """
        pass

    @command_operator
    async def returnDepositAddresses(self):
        """
        Returns all of your deposit addresses.
        """
        pass

    @command_operator
    async def generateNewAddress(self, currency):
        """
        Generates a new deposit address for the specified currency.
        """
        pass

    @command_operator
    async def returnDepositsWithdrawals(self,
                                        start=datetime.now() - timedelta(days=1),
                                        end=datetime.now()):
        """
        Returns your deposit and withdrawal history within a range, specified by the "start" and "end" POST parameters,
        both of which should be given as UNIX timestamps
        """
        pass

    @command_operator
    async def returnOpenOrders(self, currency_pair="all"):
        """
        Returns your open orders for a given market, specified by the "currencyPair" POST parameter, e.g. "BTC_XCP".
        Set "currencyPair" to "all" to return open orders for all markets.
        """
        pass

    @command_operator
    async def returnTradeHistory(self,
                                 currency_pair="all",
                                 start=datetime.now() - timedelta(days=1),
                                 end=datetime.now()):
        """
        Returns your trade history for a given market, specified by the "currencyPair" POST parameter.
        You may specify "all" as the currencyPair to receive your trade history for all markets. You may optionally
        specify a range via "start" and/or "end" POST parameters, given in UNIX timestamp format; if you do not specify
        a range, it will be limited to one day.
        """
        pass

    @command_operator
    async def returnOrderTrades(self, order_number):
        """
        Returns all trades involving a given order, specified by the "orderNumber" POST parameter. If no trades for the order
        have occurred or you specify an order that does not belong to you, you will receive an error.
        """

    @command_operator
    async def buy(self,
                  currency_pair,
                  rate,
                  amount):
        """
        Places a limit buy order in a given market. Required POST parameters are "currencyPair", "rate", and "amount".
        If successful, the method will return the order number
        """
        pass

    @command_operator
    async def sell(self,
                   currency_pair,
                   rate,
                   amount):
        """
        Places a sell order in a given market
        """
        pass

    @command_operator
    async def withdraw(self, currency, amount, address):
        """
        Immediately places a withdrawal for a given currency, with no email confirmation. In order to use this method,
        the withdrawal privilege must be enabled for your API key. Required POST parameters are "currency", "amount",
        and "address". For XMR withdrawals, you may optionally specify "paymentId".
        """
        pass

    @command_operator
    async def cancelOrder(self, order_number):
        """
        Cancels an order you have placed in a given market. Required POST parameter is "orderNumber"
        """
        pass
