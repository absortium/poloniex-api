__author__ = 'andrew.shvv@gmail.com'

import hashlib
import hmac
import json
import random
import time
import urllib
from datetime import datetime, timedelta

from poloniex import constants


def subscribe(topic):
    def decorator(handler):
        PushApi.subscribe(topic, handler)
        return handler

    return decorator


class PushApi():
    waiting_subscriptions = {}
    registred_subscriptions = {}

    def __init__(self, client):
        self.url = 'wss://api.poloniex.com'
        self.client = client

    @classmethod
    def subscribe(cls, topic, handler):
        if topic not in constants.AVAILABLE_SUBSCRIPTIONS:
            raise Exception('There is no such subscription name')

        request_id = random.randint(10 ** 14, 10 ** 15-1)
        subscription = {
            'topic': topic,
            'handler': handler,
        }

        cls.waiting_subscriptions.update({request_id: subscription})

    async def start(self, application):
        async with self.client.ws_connect(self.url, protocols=('wamp.2.json',)) as ws:
            ws.send_str(json.dumps(constants.HELLO_MSG))

            async for msg in ws:
                # TODO: Create classes for all type of messeges or stole it from autobahn
                answer = json.loads(msg.data)
                code = answer[0]

                if code == constants.MESSAGES_TYPES["SUBSCRIBED"]:
                    request_id = answer[1]
                    subscription_id = answer[2]

                    subscription = self.waiting_subscriptions[request_id]
                    subscription['request_id'] = request_id
                    self.registred_subscriptions[subscription_id] = subscription
                    del self.waiting_subscriptions[request_id]

                    if self.waiting_subscriptions is {}:
                        del self.waiting_subscriptions

                elif code == constants.MESSAGES_TYPES["WELCOME"]:
                    for request_id, subscription in self.waiting_subscriptions.items():
                        subscription_msg = [constants.MESSAGES_TYPES["SUBSCRIBE"], request_id, {},
                                            subscription['topic']]
                        subscription_msg = json.dumps(subscription_msg)
                        ws.send_str(subscription_msg)
                elif code == constants.MESSAGES_TYPES["EVENT"]:
                    subscription_id = answer[1]
                    subscription = self.registred_subscriptions[subscription_id]
                    data = answer[4]

                    handler = subscription['handler']
                    handler(application, data)

                elif code == constants.MESSAGES_TYPES["UNSUBSCRIBED"]:
                    raise Exception("UNSUBSCRIBED")
                elif code == constants.MESSAGES_TYPES["ABORT"]:
                    raise Exception("ABORT")


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
    def __init__(self, client, api_key, api_sec):

        if type(api_key) is not str:
            raise Exception('API_KEY must be string')

        if type(api_sec) is not str:
            raise Exception('SECRET_KEY must be string')

        self.api_key = api_key
        self.api_sec = api_sec.encode()
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

        e = urllib.parse.urlencode(data).encode()
        auth = {
            'Sign': hmac.new(self.api_sec, e, hashlib.sha512).hexdigest(),
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
