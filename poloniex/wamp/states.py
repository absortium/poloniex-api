__author__ = 'andrew.shvv@gmail.com'

import random

from autobahn.wamp import message

#TODO

class StateMachine():
    def __init__(self):
        self._state = Disconnected()

    def _send(self):
        self._state._send()

    def _recv(self):
        self._state._recv()

    def _recv(self):
        self._state._recv()


class State():
    def __init__(self, wamp):
        self.wamp = wamp

    def _send(self, msg):
        payload, _ = self.wamp._serializer.serialize(msg)
        self.wamp._ws.send_str(payload.decode())

    def _recv(self, s):
        messages = self.wamp._serializer.unserialize(s.encode())
        return messages[0]

    async def stop(self):
        # TODO: send stop, receive ok, close socket
        # if self._ws is not None:
        await self.wamp._ws.close()

    async def subscribe(self, handler, topic):
        request_id = random.randint(10 ** 14, 10 ** 15-1)
        subscription = {
            'topic': topic,
            'handler': handler
        }

        self.wamp._waiting_subscriptions.update({request_id: subscription})

        if self.wamp._is_connected:
            subscribe = message.Subscribe(request=request_id, topic=topic)
            self._send(subscribe)

    async def _recv(self):
        pass

    async def _send(self):
        pass

    async def _subcribe(self):
        pass

    async def _unsubscribe(self, handler, topic):
        # TODO: send unsibscibe, receive ok
        pass

    def _connect(self):
        pass

    def _disconnect(self):
        pass


class Disconnected(State):
    async def start(self):
        client = self.client
        state = self

        client._ws = await client._session.ws_connect(url=client._url, protocols=client._protocols)


        hello = message.Hello(client._realm, client._roles)
        state._send(hello)

        async for ws_msg in client._ws:
            wamp_msg = state._recv(ws_msg.data)

            wamp_handler = client.get_handler(wamp_msg.MESSAGE_TYPE)
            wamp_handler(wamp_msg)

        client._ws.close()



class Connecting(State):
    pass


class Connected(State):
    pass


class Subscribing(State):
    pass


class Subscribed(State):
    pass
