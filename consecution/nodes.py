import asyncio
import time
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor

class BaseNode:
    def __init__(self, name=''):
        self._downstream_nodes = []
        self._upstream_nodes = []
        self._queue = asyncio.Queue(2)
        self._loop = asyncio.get_event_loop()
        self.name = name
        self.executor = ThreadPoolExecutor(max_workers=1)
        #self.executor = ProcessPoolExecutor(max_workers=1)

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
        print('{} send called with {}'.format(self.name, item))
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
                    await self.process_runner(item)
                    self._queue.task_done()
            except RuntimeError:
                raise


    def push(self, item):
        if self.downstream:
            print('{} waiting till push completes'.format(self.name))
            #self.
            #self._loop.run_until_complete(self.downstream.send(item))
            #await syncio.run_coroutine_threadsafe(self.downstream.send(item))
            print('{} push done'.format(self.name))

    async def process_runner(self, item):
        print('{} starting process runner'.format(self.name))
        await self._loop.run_in_executor(self.executor, self.process, item)




    def process(self, item):

        @self.in_parallel
        def my_blocking_code(item):
            time.sleep()

        await asyncio.gather(all my block code)


        #print('{} starting process'.format(self.name))
        #nn = self.sleep_seconds if self.sleep_seconds else 0
        #print('  ' * int(10 * nn) + self.name, 'processing', item)
        #time.sleep(1)
        #print('{} pushing'.format(self.name))
        #self.push(item)
        #print(' {} done pushing'.format(self.name))



if __name__ == '__main__':
    producer = ManualProducerNode(name='producer')
    n_comps = 2
    parent = producer
    for nn in range(n_comps):
        parent = ComputeNode(upstream=parent, name='comp{:02d}'.format(nn + 1), sleep_seconds=.1 * nn)

    producer.produce_from(range(3))
    master = asyncio.gather(*producer.get_starts())


    loop = asyncio.get_event_loop()
    asyncio.ensure_future(master)
    loop.run_forever()

