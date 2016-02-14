__author__ = 'andrey.samokhvalov21@yandex.ru'

import hashlib
import hmac
import json
import random
import time
import urllib
from datetime import datetime, timedelta

from poloniex import constants


def subscribe(topic, counter=1):
    def decorator(handler):
        PushApi.subscribe(topic, handler, counter)

        return handler

    return decorator


class PushApi():
    subscriptions = {
        'footer': None,
        'ticker': None,
        'trollbox': None,
        'alerts': None,
        'heartbeat': None,
        'trades': None
    }

    def __init__(self, client):
        self.url = 'wss://api.poloniex.com'
        self.client = client

    @classmethod
    def subscribe(cls, topic, handler, counter):
        subscription = {
            'request_id': random.randint(10 ** 15, 10 ** 16-1),
            'handler': handler,
            'subscription_id': None,
            'counter': counter
        }
        if topic not in cls.subscriptions.keys():
            raise Exception('There is no such subscription name')

        cls.subscriptions.update(topic=subscription)

    async def start(self):
        async with self.client.ws_connect(self.url, protocols=('wamp.2.json',)) as ws:
            ws.send_str(json.dumps(constants.HELLO_MSG))

            welcome_msg = await ws.receive()
            welcome_msg = welcome_msg.data
            # TODO: Handle error response

            for topic, subscription in self.subscriptions.items():
                subscription_msg = [32, subscription['request_id'], {}, topic]
                ws.send_str(json.dumps(subscription_msg))

                # TODO: Handle error response
                msg = await ws.receive()
                answer = json.loads(msg.data)
                subscription_id = answer[2]
                subscription['subscription_id'] = subscription_id

            counter = 0
            async for msg in ws:
                print(msg.data)
                counter += 1
                if counter == 5:
                    break
                    # if msg.tp == aiohttp.MsgType.text:
                    #     handler(msg.data)
                    # elif msg.tp == aiohttp.MsgType.closed:
                    #     break
                    # elif msg.tp == aiohttp.MsgType.error:
                    #     break


class PublicApi():
    url = 'https://poloniex.com/public?'

    def __init__(self, client):
        self.client = client

    async def api_call(self, *args, **kwargs):
        async with self.client.get(self.url, *args, **kwargs) as response:
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


class TradingApi():
    def __init__(self, client, api_key, secret_key):

        if type(api_key) is not str:
            raise Exception('API_KEY must be string')

        if type(secret_key) is not str:
            raise Exception('SECRET_KEY must be string')

        self.api_key = api_key
        self.secret_key = secret_key.encode()
        self.client = client
        self.url = 'https://poloniex.com/tradingApi?'

    @property
    def nonce(self):
        return int(time.time() * 1000)

    async def api_call(self, *args, **kwargs):
        # set nonce parameter in data
        data = kwargs.get('data', {})
        data.update(nonce=self.nonce)
        kwargs.update(data=data)

        # encode data dict
        e = urllib.parse.urlencode(data).encode()
        auth = {
            'Sign': hmac.new(self.secret_key, e, hashlib.sha512).hexdigest(),
            'Key': self.api_key
        }

        # set auth in headers
        headers = kwargs.get('headers', {})
        headers.update(auth)
        kwargs.update(headers=headers)

        async with self.client.get(self.url, *args, **kwargs) as response:
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

        data = {
            'command': 'returnTradeHistory',
            'currencyPair': currencyPair,
            'start': time.mktime(start.timetuple()),
            'end': time.mktime(end.timetuple())
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
