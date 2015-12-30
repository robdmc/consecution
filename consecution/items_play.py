import random
from collections import defaultdict

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


##############################################################################
##############################################################################
##############################################################################
##############################################################################

class AckerEntry:
    def __init__(self, item):
        self.ack_hash = item.key
        self.item = item

    def xor_item(self, item):
        self.ack_hash = self.ack_hash ^ item.key


class Acker:
    def __init__(self, consecutor):
        self._consucutor = consecutor
        self.entry_at_key = {}
        self.anchors_keys_for_item_key = {}
        #self.item_keys_for_anchor_key = {}

    def register(self, item, anchors):
        # create an entry for the newly registered item
        self.entry_at_key[item.key] = AckerEntry(item)

        # assemble a list of all anchor keys for this item
        self.anchors_keys_for_item_key[item.key] = [
            anchor.key for anchor in anchors
        ]

        # xor this item with each of its anchors
        for anchor in anchors:
            self.entry_at_key[anchor.key].xor_item(item)

    def ack(self, item):
        # get the entry for this item, and xor it again for acking
        entry = self.entry_at_key[item.key]
        entry.xor_item(item)

        # now ack this item for all its anchors
        for anchor_key in self.anchors_keys_for_item_key[item.key]:
            entry = self.entry_at_key[anchor_key]
            entry.xor_item(item)
            if entry.ack_hash == 0:
                del self.entry_at_key[anchor_key]

        # if entry is acked, delete it
        if entry.ack_hash == 0:
            del self.entry_at_key[item.key]
            del self.anchors_keys_for_item_key[item.key]




class Item:
    def __init__(self, acker, anchors, value=None):
        self.key = random.getrandbits(160)
        self.acker = acker
        self.acker.register(self, anchors)

    def ack(self):
        self.acker.ack(self)





















