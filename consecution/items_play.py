def worker_func(item, state):
    return item, state



class Mapper(ProcessingNode):
    async def process(self, item):
        out_item = Item(anchor=item)
        out_item.value = 1
        await self.push(out_item)

class Expander(ProcessingNode):
    async def process(self, item):
        out_list = []
        for nn in range(10):
            out_item = Item(anchor=item, value=1)
            await self.push(out_item)

class Reducer(ProcessingNode):
    async def begin(self):
        self.state.update(*args, **kwargs)
    async def process(self, item):




