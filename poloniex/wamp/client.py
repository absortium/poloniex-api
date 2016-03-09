import random

import logging

from autobahn.wamp import message
from autobahn.wamp.role import DEFAULT_CLIENT_ROLES
from autobahn.wamp.serializer import JsonSerializer

from poloniex.logger import LogMixin

__author__ = 'andrew.shvv@gmail.com'


class WAMPClient(LogMixin):
    def __init__(self,
                 url,
                 session,
                 roles=DEFAULT_CLIENT_ROLES,
                 realm='realm1',
                 protocols=('wamp.2.json',),
                 serializer=JsonSerializer()):
        self._url = url
        self._session = session
        self._protocols = protocols
        self._realm = realm
        self._roles = roles
        self._serializer = serializer
        self._ws = None
        self._is_connected = False
        self._handlers = {
            message.Welcome.MESSAGE_TYPE: self._on_welcome,
            message.Subscribed.MESSAGE_TYPE: self._on_subscribed,
            message.Event.MESSAGE_TYPE: self._on_event,
        }

        self._waiting_subscriptions = {}
        self._registered_subscriptions = {}
        self.logger.setLevel(logging.DEBUG)

    def get_handler(self, message_type):

        handler = self._handlers.get(message_type)
        if handler is None:
            handler = self._on_other
        return handler

    @property
    def subsciptions(self):
        return [self._waiting_subscriptions, self._registered_subscriptions]

    async def _on_welcome(self, msg):
        self._is_connected = True
        for request_id, subsciption in self._waiting_subscriptions.items():
            topic = subsciption['topic']
            subscribe = message.Subscribe(request=request_id, topic=topic)
            self._send(subscribe)

    async def _on_event(self, event):
        subscription_id = event.subscription
        subscription = self._registered_subscriptions[subscription_id]

        handler = subscription['handler']
        await handler(event.args)

    async def _on_subscribed(self, msg):
        request_id = msg.request
        subscription_id = msg.subscription

        subscription = self._waiting_subscriptions[request_id]
        subscription['request_id'] = request_id
        self._registered_subscriptions[subscription_id] = subscription
        del self._waiting_subscriptions[request_id]

    async def _on_other(self, msg):
        raise Exception("Unimplemented handler")

    def _send(self, msg):
        payload, _ = self._serializer.serialize(msg)
        self._ws.send_str(payload.decode())

    def _recv(self, s):
        messages = self._serializer.unserialize(s.encode())
        return messages[0]

    async def start(self):
        async with self._session.ws_connect(url=self._url, protocols=self._protocols) as ws:
            self._ws = ws

            hello = message.Hello(self._realm, self._roles)
            self._send(hello)

            async for ws_msg in ws:
                wamp_msg = self._recv(ws_msg.data)
                wamp_handler = self.get_handler(wamp_msg.MESSAGE_TYPE)
                await wamp_handler(wamp_msg)

    async def stop(self):
        # TODO: send stop, receive ok, close socket
        # if self._ws is not None:
        await self._ws.close()

    async def subscribe(self, handler, topic):
        request_id = random.randint(10 ** 14, 10 ** 15-1)
        subscription = {
            'topic': topic,
            'handler': handler
        }

        self._waiting_subscriptions.update({request_id: subscription})

        if self._is_connected:
            subscribe = message.Subscribe(request=request_id, topic=topic)
            self._send(subscribe)

    async def unsubscribe(self, handler, topic):
        # TODO: send unsibscibe, receive ok
        pass
