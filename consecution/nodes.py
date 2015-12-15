import traceback
import asyncio
import pickle
import sys
import time
import inspect
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from functools import partial


class BaseNode:
    #executor = ProcessPoolExecutor(max_workers=10)
    executor = ThreadPoolExecutor(max_workers=10)

    def __init__(self, name=''):
        self._downstream_nodes = []
        self._upstream_nodes = []
        self._queue = asyncio.Queue(2)
        self._loop = asyncio.get_event_loop()
        self.name = name

    @property
    def downstream(self):
        return self._downstream_nodes[0] if self._downstream_nodes else None

    @property
    def upstream(self):
        return self._upstream_nodes[0] if self._upstream_nodes else None

    def add_downstream_node(self, *other_nodes):
        self._downstream_nodes.extend(other_nodes)
        for other in other_nodes:
            other._upstream_nodes.extend([self])

    def add_upstream_node(self, *other_nodes):
        self._upstream_nodes.extend(other_nodes)
        for other in other_nodes:
            other._downstream_nodes.extend([self])

    async def send(self, item):
        await self._queue.put(item)

    async def complete(self):
        await self._queue.join()
        for child_node in self._downstream_nodes:
            await child_node.complete()

    async def start(self):
        pass

    def get_starts(self):
        starts = [self.start()]
        for child in self._downstream_nodes:
            starts.extend(child.get_starts())
        return starts

class EndSentinal:
    def __str__(self):
        return 'sentinal'


class ManualProducerNode(BaseNode):
    def __init__(self, name=''):
        super(ManualProducerNode, self).__init__(name=name)

    def produce_from(self, iterable):
        self.iterable = iterable

    async def start(self):
        if not self.downstream:
            raise ValueError(
                'Can\'t start a producer without something to consume it')
        for value in self.iterable:
            await self.downstream.send(value)
        await self.downstream.send(EndSentinal())
        await self.complete()
        self._loop.stop()

    def send(self):
        raise NotImplementedError('Producers don\'t have send methods')




class ComputeNode(BaseNode):
    def __init__(self, upstream=None, downstream=None, name='', sleep_seconds=None):
        super(ComputeNode, self).__init__(name=name)
        self.sleep_seconds = sleep_seconds
        if upstream:
            self.add_upstream_node(upstream)
        if downstream:
            self.add_downstream_node(downstream)

    async def start(self):
        while True:
            try:
                item = await self._queue.get()
                if isinstance(item, EndSentinal):
                    if self.downstream:
                        await self.downstream.send(item)
                    self._queue.task_done()
                    break
                else:
                    await self.process(item)
                    self._queue.task_done()
            except RuntimeError:
                raise

    async def push(self, item):
        if self.downstream:
            await self.downstream.send(item)

    async def make_task(self, function, *args, **kwargs):
        """
        returns succeeded, result
        """

        def error_wrapper(*args, **kwargs):
            try:
                return (True, function(*args, **kwargs))
            except:
                return (False, sys.exc_info())

        func_to_exec = partial(error_wrapper, *args, **kwargs)
        return self._loop.run_in_executor(self.executor, func_to_exec)

    async def run_parallel(self, *tasks, log_errors=True):
        """
        may want to take log_errors from a class variable instead of
        a function argument
        """
        futures = await asyncio.gather(*tasks)
        results = []
        for result in futures:
            #succeeded, val = await res
            results.append(await result)
        if log_errors:
            for (success, value) in results:
                if not success:
                    print('-' * 80, file=sys.stderr)
                    traceback.print_tb(value[2], file=sys.stderr)
                    print(file=sys.stderr)
                    print(value[0], file=sys.stderr)
                    print(value[1], file=sys.stderr)
                    print('-' * 80, file=sys.stderr)

        return results


    async def process(self, item):

        my_var = 'silly'

        def my_blocking_code1(name, item):
            time.sleep(1)
            print('{} executing block1 on {}'.format(name, item))
            #return 'ret_from_block1'

        def my_blocking_code2(name, item):
            print('{} executing block2 on {}'.format(name, item))
            #raise ValueError('my error')
            1 / 0
            time.sleep(1)
            return ('result2', self.name, item)


        """
        I don't like the name make_task.  I want to find other language
        for this that doesn't overlap with asyncio names.
        maybe self.parallel_wrap
        or    self.make_parallel
        or self.in_parallel
        """

        task1 = self.make_task(my_blocking_code1, self.name, item)
        task2 = self.make_task(my_blocking_code2, self.name, item)

        results = await self.run_parallel(task1, task2)
        for res in results:
            print(res)

        await self.push(item)

        """
        Got decent error handling in the executed function.
        Next step is to nicely handle errors in this process function
        Maybe make the error logging a class-based thing.

        Would like to see how things work for processes as well as threads
        """



if __name__ == '__main__':
    producer = ManualProducerNode(name='producer')
    n_comps = 1
    parent = producer
    for nn in range(n_comps):
        parent = ComputeNode(upstream=parent, name='comp{:02d}'.format(nn + 1), sleep_seconds=.1 * nn)

    producer.produce_from(range(1))
    master = asyncio.gather(*producer.get_starts())


    loop = asyncio.get_event_loop()
    asyncio.ensure_future(master)
    loop.run_forever()

