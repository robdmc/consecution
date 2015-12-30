import random

class State:
    def __init__(self):
        self._state = {}

    def update(self, **kwargs):
        for key, func in kwargs.items():
            current_obj = self._state.get(key, None)
            self._state[key] = func(current_obj)

    def get(self, key):
        return copy.deepcopy(self._state.get(key, None))



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
        self.multi_anchor.clear()
        await self.state.update(count=lambda: 0)

    async def process(self, item):
        await self.multi_anchor.add(item)
        await self.state.update(count=lambda count: count + 1)

    async def end(self):
        out_item = Item(anchor=self.multi_anchor, value=self.state.get('count'))
        self.push(out_item)

class AckerEntry:
    def __init__(self, item):
        self.hashed_keys = item.key

    def xor_item(self, item):
        self.hashed_keys = self.hashed_keys ^ item.key


class Acker:
    def __init__(self, consecutor):
        self._consucutor = consecutor
        self.entry_at_key = {}
        self.anchors_keys_for_item_key = {}
        self.item_keys_for_anchor_key = {}



    def register(self, item, anchors):
        self.item_at_key.update({item.key: AckerEntry(item})
        for anchor in anchors:
            self.item_at_key[anchor.key].xor_item(item)



class Item:
    def __init__(self, acker, anchor, value=None):
        self.key = random.getrandbits(160)
        self.acker = acker
        self.acker.register(self, anchor)

    #def add_parerent(self, item):
    #    self._parents.append(item)





















