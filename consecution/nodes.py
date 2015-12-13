import asyncio

class BaseNode:
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
    def __init__(self, upstream=None, downstream=None, name='', sleep=None):
        super(ComputeNode, self).__init__(name=name)
        self.sleep = sleep
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


    async def process(self, item):
        # would really like this to not be async and actually called in 
        # a separate thread (or process) so that it can have blocking code
        nn = self.sleep if self.sleep else 0
        print('  ' * int(10 * nn) + self.name, 'processing', item)
        if self.downstream:
            if self.sleep:
                await asyncio.sleep(self.sleep)
            await self.downstream.send(item)


if __name__ == '__main__':
    producer = ManualProducerNode(name='producer')
    n_comps = 2
    parent = producer
    for nn in range(n_comps):
        parent = ComputeNode(upstream=parent, name='comp{:02d}'.format(nn + 1), sleep=.1 * nn)
    #comp1 = ComputeNode(upstream=producer, name='comp1')
    #comp2 = ComputeNode(upstream=comp1, name='comp2')

    producer.produce_from(range(3))
    master = asyncio.gather(*producer.get_starts())


    loop = asyncio.get_event_loop()
    asyncio.ensure_future(master)
    loop.run_forever()


#
#
#
#
#class PNode(ProcessorNode):
#    def __init__(self, name, *args, **kwargs):
#        super(PNode, self).__init__(*args, **kwargs)
#        self.name = name
#
#    async def process(self):
#        #print('starting p', self.upstream)
#        async for item in self.upstream:
#            out = ((self.name, item))
#            await self.downstream.push(out)
#
#class FNode(ProcessorNode):
#    def __init__(self, name, *args, **kwargs):
#        super(FNode, self).__init__(*args, **kwargs)
#        self.name = name
#
#    async def process(self):
#        #print('starting f', self.upstream)
#        async for item in self.upstream:
#            #print('looping')
#            out = ((self.name, item))
#            print(out)
#
#
#async def myfunc():
#    return 'myret'
#
#async def main():
#    gen = (nn for nn in range(3))
#    producer = ProducerNode(gen)
#    p1 = PNode(name='p1', upstream=producer)
#    f2 = FNode(name='f2', upstream=p1)
#    await producer.start()
#    await p1.process()
#    await f2.process()
#
#"""
#I THINK I NEED TO DEFINE ANOTHER KIND OF NODE.  SO BASICALLY, I'LL HAVE
#THREE KINDS OF NODES:  PRODUCER, PROCESSOR, AND CONSUMER.
#PRODUCERS AND PROCESSORS JUST EXPOSE ITERATORS WHEREAS CONSUMERS LOOP
#OVER THESE EXPOSED ITERATORS.
#"""
#
#    #async for item in p1:
#    #    print(item)
#
#
#    #async for item in producer:
#    #    print(('a', item))


