import traceback
import asyncio
import pickle
import sys
import time
import inspect
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from functools import partial


async def process(item):
        print('processing {}'.format(item))
        await asyncio.sleep(1)


class EndSentinal:
    def __str__(self):
        return 'sentinal'
    def __repr__(self):
        return self.__str__()

class Processor:
    def __init__(self):
        self._queue = asyncio.Queue(2)

    async def push(self, item):
        await asyncio.Task(self._queue.put(item))


    async def start(self):
        while True:
            item = await self._queue.get()
            if isinstance(item, EndSentinal):
                self._queue.task_done()
                await self._queue.join()
                break
            else:
                await process(item)
                self._queue.task_done()

class Consecutor:
    def __init__(self):
        self.proc = Processor()

    def get_starts(self):
        return [self._start(), self.proc.start()]

    async def _start(self):

        for item in self.iterable:
            await self.proc.push(item)
        await self.proc.push(EndSentinal())

    def consume_from_iterable(self, iterable):
        self.iterable = iterable
        loop = asyncio.get_event_loop()
        loop.run_until_complete(asyncio.gather(*self.get_starts()))

    def push(self, item):
        self.consume_from_iterable([item])


if __name__ == '__main__':
    print('runnin it')

    c = Consecutor()
    iterable = [1, 2, 3]
    c.consume_from_iterable(iterable)
    iterable = [4, 5, 6]
    c.consume_from_iterable(iterable)

    c = Consecutor()
    for item in range(4):
        c.push(item)
    print('done')






    #def run_it():
    #    async def func():
    #        print('running async')

    #    new_loop = asyncio.new_event_loop()
    #    asyncio.set_event_loop(new_loop)

    #    loop = asyncio.get_event_loop()
    #    loop.run_until_complete(asyncio.Task(func()))
    #    print(id(new_loop))
    #    print(id(loop))

    #run_it()

