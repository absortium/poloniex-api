__author__ = 'andrew.shvv@gmail.com'


class PoloniexError(Exception): pass


class AsyncError(PoloniexError): pass


class AddressAlreadyExist(PoloniexError): pass
