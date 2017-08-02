from datetime import datetime
from datetime import timedelta

import requests

from poloniex.error import PoloniexError
from poloniex.api.base import command_operator, BasePublicApi, BaseTradingApi

__author__ = 'andrew.shvv@gmail.com'


class PublicApi(BasePublicApi):
    url = "https://poloniex.com/public?"

    def api_call(self, *args, **kwargs):
        response = requests.get(self.url, *args, **kwargs)

        if response.status_code == 200:
            return response.json()
        else:
            raise PoloniexError('Got {} when calling {}.'.format(response.status_code, self.url))

    @command_operator
    def returnTicker(self):
        """
        Returns the ticker for all markets
        """
        pass

    @command_operator
    def return24hVolume(self):
        """
        Returns the 24-hour volume for all markets, plus totals for primary currencies.
        """
        pass

    @command_operator
    def returnOrderBook(self, currency_pair="all", depth=50):
        """
        Returns the order book for a given market, as well as a sequence number for use with the Push API and an indicator
        specifying whether the market is frozen. You may set currencyPair to "all" to get the order books of all markets
        """
        pass

    @command_operator
    def returnChartData(self,
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
    def returnCurrencies(self):
        """
        Returns information about currencies
        """
        pass

    @command_operator
    def returnTradeHistory(self,
                           currency_pair="all",
                           start=datetime.now() - timedelta(days=1),
                           end=datetime.now()):
        """
        Returns the past 200 trades for a given market, or up to 50,000 trades between a range specified in UNIX timestamps
        by the "start" and "end" GET parameters.
        """
        pass


class TradingApi(BaseTradingApi):
    url = "https://poloniex.com/tradingApi?"

    def api_call(self, *args, **kwargs):
        data, headers = self.secure_request(kwargs.get('data', {}), kwargs.get('headers', {}))

        kwargs['data'] = data
        kwargs['headers'] = headers

        response = requests.post(self.url, *args, **kwargs)
        if response.status_code == 200:
            return response.json()
        else:
            raise PoloniexError('Got {} when calling {}.'.format(response.status_code, self.url))

    @command_operator
    def returnBalances(self):
        """
        Returns all of your available balances
        """
        pass

    @command_operator
    def returnCompleteBalances(self):
        """
        Returns all of your balances, including available balance, balance on orders, and the estimated BTC value of your balance.
        """
        pass

    @command_operator
    def returnDepositAddresses(self):
        """
        Returns all of your deposit addresses.
        """
        pass

    @command_operator
    def generateNewAddress(self, currency):
        """
        Generates a new deposit address for the specified currency.
        """
        pass

    @command_operator
    def returnDepositsWithdrawals(self,
                                  start=datetime.now() - timedelta(days=1),
                                  end=datetime.now()):
        """
        Returns your deposit and withdrawal history within a range, specified by the "start" and "end" POST parameters,
        both of which should be given as UNIX timestamps
        """
        pass

    @command_operator
    def returnOpenOrders(self, currency_pair="all"):
        """
        Returns your open orders for a given market, specified by the "currencyPair" POST parameter, e.g. "BTC_XCP".
        Set "currencyPair" to "all" to return open orders for all markets.
        """
        pass

    @command_operator
    def returnTradeHistory(self,
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
    def returnOrderTrades(self, order_number):
        """
        Returns all trades involving a given order, specified by the "orderNumber" POST parameter. If no trades for the order
        have occurred or you specify an order that does not belong to you, you will receive an error.
        """

    @command_operator
    def buy(self,
            currency_pair,
            rate,
            amount):
        """
        Places a limit buy order in a given market. Required POST parameters are "currencyPair", "rate", and "amount".
        If successful, the method will return the order number
        """
        pass

    @command_operator
    def sell(self,
             currency_pair,
             rate,
             amount):
        """
        Places a sell order in a given market
        """
        pass

    @command_operator
    def withdraw(self, currency, amount, address):
        """
        Immediately places a withdrawal for a given currency, with no email confirmation. In order to use this method,
        the withdrawal privilege must be enabled for your API key. Required POST parameters are "currency", "amount",
        and "address". For XMR withdrawals, you may optionally specify "paymentId".
        """
        pass

    @command_operator
    def cancelOrder(self, order_number):
        """
        Cancels an order you have placed in a given market. Required POST parameter is "orderNumber" 
        """
        pass
