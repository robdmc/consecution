import traceback
import asyncio
import pickle
import sys
import time
import inspect
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from functools import partial



#############################################################
def my_blocking_code1(name, item):
    time.sleep(1)
    print('{} executing block1 on {}'.format(name, item))
    #return 'ret_from_block1'

def my_blocking_code2(name, item):
    print('{} executing block2 on {}'.format(name, item))
    time.sleep(1)
    return ('result2', name, item)

#############################################################

def error_wrapper(f, log_errors, *args, **kwargs):
        try:
            return (True, f(*args, **kwargs))
        except:
            if log_errors:
                log_errors(sys.exc_info())
            return (False, sys.exc_info())

async def make_job(function, node_obj, *args, **kwargs):
    """
    returns succeeded, result
    """
    func_to_exec = partial(
        error_wrapper, function, node_obj._log_errors, *args, **kwargs)
    return node_obj._loop.run_in_executor(node_obj.executor, func_to_exec)

#############################################################

def log_errors(exc_info_tup):
    print('v' * 78, file=sys.stderr)
    traceback.print_tb(exc_info_tup[2], file=sys.stderr)
    print(file=sys.stderr)
    print(exc_info_tup[0], file=sys.stderr)
    print(exc_info_tup[1], file=sys.stderr)
    print('^' * 78, file=sys.stderr)

class BaseNode:
    executor = ProcessPoolExecutor(max_workers=10)
    #executor = ThreadPoolExecutor(max_workers=10)

    def __init__(
            self, name='', log_errors=True, loop=None, upstream=None,
            downstream=None):




        self._downstream_nodes = []
        self._upstream_nodes = []
        self._queue = asyncio.Queue(2)
        self._loop = loop if loop else asyncio.get_event_loop()
        self._log_errors = log_errors
        self.name = name

        if upstream:
            self.add_upstream_node(upstream)
        if downstream:
            self.add_downstream_node(downstream)

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


    async def complete(self):
        await self._queue.join()
        for child_node in self._downstream_nodes:
            await child_node.complete()

    async def add_to_queue(self, item):
        await self._queue.put(item)

    async def push(self, item):
        if self.downstream:
            await self.downstream.add_to_queue(item)

    async def start(self):
        while True:
            try:  # experiment with removing this try block 'cause I don't remember why it's here
                item = await self._queue.get()
                if isinstance(item, EndSentinal):
                    if self.downstream:
                        await self.downstream.add_to_queue(item)
                    self._queue.task_done()
                    break
                else:
                    try:
                        await self.process(item)
                        self._queue.task_done()
                    except:
                        self._queue.task_done()
                        if self._log_errors:
                            log_errors(sys.exc_info())

            except RuntimeError:
                raise


    def get_starts(self):
        starts = [self.start()]
        for child in self._downstream_nodes:
            starts.extend(child.get_starts())
        return starts

class EndSentinal:
    def __str__(self):
        return 'sentinal'


class ManualProducerNode(BaseNode):
    def __init__(self, *args, **kwargs):
        super(ManualProducerNode, self).__init__(*args, **kwargs)

    #def __init__(self, name='', log_errors=True, loop=None):
    #    super(ManualProducerNode, self).__init__(
    #        name='', log_errors=log_errors, loop=loop
    #    )

    def produce_from(self, iterable):
        self.iterable = iterable

    async def start(self):
        if not self.downstream:
            raise ValueError(
                'Can\'t start a producer without something to consume it')
        for value in self.iterable:
            await self.downstream.add_to_queue(value)
        await self.downstream.add_to_queue(EndSentinal())
        await self.complete()
        self._loop.stop()

    def add_to_queue(self):
        raise NotImplementedError('Producers don\'t have send methods')


class ComputeNode(BaseNode):
    def __init__(self, *args, **kwargs):
        super(ComputeNode, self).__init__(*args, **kwargs)

    async def make_job(self, function, *args, **kwargs):
        return await make_job(function, self, *args, **kwargs)

    async def exececute_in_parallel(self, *tasks, log_errors=True):
        """
        may want to take log_errors from a class variable instead of
        a function argument
        """
        futures = await asyncio.gather(*tasks)
        results = []
        for result in futures:
            results.append(await result)
        return results


    async def process(self, item):

        #def my_blocking_code1(name, item):
        #    time.sleep(1)
        #    print('{} executing block1 on {}'.format(name, item))
        #    #return 'ret_from_block1'

        #def my_blocking_code2(name, item):
        #    print('{} executing block2 on {}'.format(name, item))
        #    time.sleep(1)
        #    return ('result2', self.name, item)

        job1 = self.make_job(my_blocking_code1, self.name, item)
        job2 = self.make_job(my_blocking_code2, self.name, item)

        results = await self.exececute_in_parallel(job1, job2)
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
        parent = ComputeNode(upstream=parent, name='comp{:02d}'.format(nn + 1))

    producer.produce_from(range(1))
    master = asyncio.gather(*producer.get_starts())


    loop = asyncio.get_event_loop()
    asyncio.ensure_future(master)
    loop.run_forever()

