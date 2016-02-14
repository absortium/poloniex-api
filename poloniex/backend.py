
import asyncio

from os import environ
from autobahn.asyncio.wamp import ApplicationSession, ApplicationRunner


class Component(ApplicationSession):
    """
    An application component that publishes an event every second.
    """

    @asyncio.coroutine
    def onJoin(self, details):
        counter = 0
        while True:
            print("publish: com.myapp.topic1", counter)
            self.publish(u'com.myapp.topic1', counter)
            counter += 1
            yield from asyncio.sleep(1)



runner = ApplicationRunner("ws://127.0.0.1:8080/ws", "crossbardemo", debug=True)
runner.run(Component)