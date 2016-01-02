import traceback
import asyncio
import pickle
import sys
import time
import inspect
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from functools import partial

class Processor:
    def __init__(self):
        self.reset()

    def reset(self):
        self.input_iterable = []
        self.output_list = []

    def consume_from(self, iterable):
        self.input_iterable = iterable

    async def _start(self):
        self.output_list.extend([('done', v) for v in self.input_iterable])

    def run(self):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self._start())

    def push(self, value):
        self.consume_from([value])
        self.run()


if __name__ == '__main__':
    if False:
        p = Processor()
        p.consume_from(range(10))
        p.run()
        for v in p.output_list:
            print(v)
    if True:
        p = Processor()
        p.push('a')
        p.push('b')
        for v in p.output_list:
            print(v)


