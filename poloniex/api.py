__author__ = 'andrew.shvv@gmail.com'

import hashlib
import hmac
import logging
import time
import urllib
from datetime import datetime, timedelta

from poloniex.logger import LogMixin

from poloniex.wamp.client import WAMPClient
from poloniex import constants


class PushApi(WAMPClient):
    url = 'wss://api.poloniex.com'

    def __init__(self, session):
        LogMixin.__init__(self)
        WAMPClient.__init__(self, url=self.url, session=session)

    def _ticker(self, handler):
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
                'currency_pair': currency_pair,
                'last': last,
                'lowest_ask': lowest_ask,
                'highest_bid': highest_bid,
                'percent_change': percent_change,
                'base_volume': base_volume,
                'quote_volume': quote_volume,
                'is_frozen': is_frozen,
                'day_high': day_high,
                'day_low': day_low
            }

            await handler(**kwargs)

        return decorator

    def _trades(self, handler):
        async def decorator(data):
            for event in data:
                await handler(**event)

        return decorator

    def _trollbox(self, handler):
        async def decorator(data):
            self.logger.debug(data)

            if len(data) != 5:
                return

            type_ = data[0]
            message_id = data[1]
            username = data[2]
            text = data[3]
            reputation = data[4]

            kwargs = {
                'id': message_id,
                'username': username,
                'type': type_,
                'text': text,
                'reputation': reputation
            }

            await handler(**kwargs)

        return decorator

    async def subscribe(self, topic, handler):
        if topic in constants.CURRENCY_PAIRS:
            wrapped_handler = self._trades(handler)
            await super().subscribe(topic=topic, handler=wrapped_handler)

        elif topic is "trollbox":
            wrapped_handler = self._trollbox(handler)
            await super().subscribe(topic=topic, handler=wrapped_handler)

        elif topic is "ticker":
            wrapped_handler = self._ticker(handler)
            await super().subscribe(topic=topic, handler=wrapped_handler)

        elif topic in constants.AVAILABLE_SUBSCRIPTIONS:
            await super().subscribe(topic=topic, handler=handler)

        else:
            raise Exception('Topic not available')


class PublicApi(LogMixin):
    url = 'https://poloniex.com/public?'

    def __init__(self, session, level=logging.DEBUG):
        super().__init__()
        self.session = session
        self.logger.setLevel(level)

    async def api_call(self, *args, **kwargs):
        self.logger.debug(kwargs)
        async with self.session.get(self.url, *args, **kwargs) as response:
            response = await response.json()

            if ('error' in response) and (response['error'] is not None):
                raise Exception(response['error'])

            return response

    async def returnTicker(self):
        params = {
            'command': 'returnTicker'
        }

        return await self.api_call(params=params)

    async def return24Volume(self):
        params = {
            'command': 'return24hVolume'
        }

        return await self.api_call(params=params)

    async def returnOrderBook(self, currencyPair='all', depth=50):
        if (currencyPair != 'all') and (currencyPair not in constants.CURRENCY_PAIRS):
            raise Exception('currencyPair: {} not available'.format(currencyPair))

        params = {
            'command': 'returnOrderBook',
            'currencyPair': currencyPair,
            'depth': depth
        }

        return await self.api_call(params=params)

    async def returnChartData(self,
                              currencyPair,
                              start=datetime.now()-timedelta(days=1),
                              end=datetime.now(),
                              period=300):
        params = {
            'command': 'returnChartData',
            'currencyPair': currencyPair,
            'period': period,
            'start': time.mktime(start.timetuple()),
            'end': time.mktime(end.timetuple())
        }

        if period not in constants.CHART_DATA_PERIODS:
            raise Exception("Wrong period")

        return await self.api_call(params=params)

    async def returnCurrencies(self):
        params = {
            'command': 'returnCurrencies'
        }

        return await self.api_call(params=params)

    async def returnTradeHistory(self,
                                 currencyPair='all',
                                 start=datetime.now()-timedelta(days=1),
                                 end=datetime.now()):
        'Returns the past 200 trades for a given market, or all of the trades between a range' \
        'specified in UNIX timestamps by the "start" and "end" GET parameters.'

        params = {
            'command': 'returnTradeHistory',
            'currencyPair': 'BTC_NXT',
            'start': int(time.mktime(start.timetuple())),
            'end': int(time.mktime(end.timetuple()))
        }

        return await self.api_call(params=params)


class TradingApi(LogMixin):
    url = 'https://poloniex.com/tradingApi?'

    def __init__(self, session, api_key, api_sec):

        if type(api_key) is not str:
            raise Exception('API_KEY must be string')

        if type(api_sec) is not str:
            raise Exception('SECRET_KEY must be string')

        self.api_key = api_key
        self.api_sec = api_sec.encode()
        self.session = session

    @property
    def nonce(self):
        return int(time.time() * 1000)

    async def api_call(self, *args, **kwargs):
        # set nonce parameter in data
        data = kwargs.get('data', {})
        data.update(nonce=self.nonce)
        kwargs.update(data=data)

        e = urllib.parse.urlencode(data).encode()
        auth = {
            'Sign': hmac.new(self.api_sec, e, hashlib.sha512).hexdigest(),
            'Key': self.api_key
        }

        # set auth in headers
        headers = kwargs.get('headers', {})
        headers.update(auth)
        kwargs.update(headers=headers)

        async with self.session.post(self.url, *args, **kwargs) as response:
            response = await response.json()
            if ('error' in response) and (response['error'] is not None):
                raise Exception(response['error'])

            return response

    async def returnBalances(self, currencies=['BTC', 'ETH']):
        'Returns all of your available balances'

        data = {
            'command': 'returnBalances',
        }

        response = await self.api_call(data=data)

        # filter currencies
        response = {currency: balance for currency, balance in response.items() if currency in currencies}
        return response

    async def returnCompleteBalances(self, currencies=['BTC', 'ETH']):
        'Returns all of your balances, including available balance, balance on orders, and the estimated BTC value of your balance.'

        data = {
            'command': 'returnCompleteBalances'
        }

        response = await self.api_call(data=data)

        # filter currencies
        response = {currency: balance for currency, balance in response.items() if currency in currencies}
        return response

    async def returnDepositAddresses(self, currencies=['BTC', 'ETH']):
        'Returns all of your deposit addresses.'

        data = {
            'command': 'returnDepositAddresses'
        }

        response = await self.api_call(data=data)

        # filter currencies
        response = {currency: address for currency, address in response.items() if currency in currencies}
        return response

    async def generateNewAddress(self, currency):
        'Generates a new deposit address for the currency specified by the "currency" POST parameter.'

        data = {
            'command': 'generateNewAddress',
            'currency': currency,
        }

        response = await self.api_call(data=data)

        if response['success'] == 0:
            if 'address' in response:
                raise Exception(response['address'])
            elif 'response' in response:
                raise Exception(response['response'])

        return response

    async def returnDepositsWithdrawals(self, start=datetime.now()-timedelta(days=1), end=datetime.now()):
        'Returns your deposit and withdrawal history within a range, specified by the "start" and "end"' \
        'POST parameters, both of which should be given as UNIX timestamps.'

        data = {
            'command': 'returnDepositsWithdrawals',
            'start': time.mktime(start.timetuple()),
            'end': time.mktime(end.timetuple())
        }

        return await self.api_call(data=data)

    async def returnOpenOrders(self, currencyPair='all'):
        'Returns your open orders for a given market, specified by the "currencyPair" POST parameter,' \
        'e.g. "BTC_XCP". Set "currencyPair" to "all" to return open orders for all markets.'

        if currencyPair != 'all':
            if currencyPair not in constants.CURRENCY_PAIRS:
                raise Exception('currencyPair: {} not available'.format(currencyPair))

        data = {
            'command': 'returnOpenOrders',
            'currencyPair': currencyPair
        }

        return await self.api_call(data=data)

    async def returnTradeHistory(self,
                                 currencyPair='all',
                                 start=datetime.now()-timedelta(days=1),
                                 end=datetime.now()):
        'Returns your trade history for a given market, specified by the "currencyPair" POST parameter.' \
        'You may specify "all" as the currencyPair to receive your trade history for all markets.' \
        'You may optionally specify a range via "start" and/or "end" POST parameters, given in UNIX timestamp format'

        start = int(time.mktime(start.timetuple()))
        end = int(time.mktime(end.timetuple()))

        data = {
            'command': 'returnTradeHistory',
            'currencyPair': currencyPair,
            'start': start,
            'end': end
        }

        return await self.api_call(data=data)

    async def buy(self, currencyPair, rate, amount):
        if currencyPair not in constants.CURRENCY_PAIRS:
            raise Exception('currencyPair: {} not available'.format(currencyPair))

        data = {
            'command': 'buy',
            'rate': rate,
            'currencyPair': currencyPair,
            'amount': amount
        }

        return await self.api_call(data=data)

    async def sell(self, currencyPair, rate, amount):
        if currencyPair not in constants.CURRENCY_PAIRS:
            raise Exception('currencyPair: {} not available'.format(currencyPair))

        data = {
            'command': 'sell',
            'rate': rate,
            'currencyPair': currencyPair,
            'amount': amount
        }

        # TODO: save order

        return await self.api_call(data=data)

    async def cancelOrder(self, orderNumber):
        # TODO: check that orderNumber exist

        data = {
            'command': 'cancelOrder',
            'orderNumber': orderNumber
        }

        return await self.api_call(data=data)

    async def moveOrder(self):
        data = {
            'command': 'moveOrder'
        }

        return await self.api_call(data=data)
