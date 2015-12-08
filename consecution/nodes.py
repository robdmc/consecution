import asyncio

class BaseNode:
    def __init__(self):
        self._downstream_nodes = []
        self._upstream_nodes = []
        self._queue = asyncio.Queue(3)

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




class ManualProducerNode(BaseNode):
    def __init__(self):
        super(ManualProducerNode, self).__init__()

    async def produce_from(self, iterable):
        if not self.downstream:
            raise ValueError(
                'Can\'t start a producer without something to consume it')
        for value in iterable:
            print
            print('ierating over', value)
            await self.downstream.send(value)

    def send(self):
        raise NotImplementedError('Producers don\'t have send methods')




class ComputeNode(BaseNode):
    def __init__(self, upstream=None, downstream=None):
        super(ComputeNode, self).__init__()
        if upstream:
            self.add_upstream_node(upstream)
        if downstream:
            self.add_downstream_node(downstream)

    async def start(self):
        while True:
            item = await self._queue.get()
            self.process(item)

    def process(self, item):
        print('processing', item)
        #raise NotImplementedError('you must define a process() method')

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


