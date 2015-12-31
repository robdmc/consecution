import random

class AckerEntry:
    def __init__(self, item):
        self.ack_hash = item.key
        self.item = item

    def xor_item(self, item):
        self.ack_hash = self.ack_hash ^ item.key


class Acker:
    def __init__(self):
        self.entry_at_key = {}
        self.anchor_keys_for_item_key = {}

    def register(self, item, anchor=None):
        # create an entry for the newly registered item
        self.entry_at_key[item.key] = AckerEntry(item)

        if anchor:
            self.add_anchor(item, anchor)

    def add_anchor(self, item, anchor):
        self.anchor_keys_for_item_key[item.key].append(anchor.key)
        self.entry_at_key[anchor.key].xor_item(item)

    def ack(self, item):
        # ack this item for all its anchors
        for anchor_key in self.anchor_keys_for_item_key[item.key]:
            self.entry_at_key[anchor_key].xor_item(item)

        # ack the current item by xor with itself
        item_entry = self.entry_at_key[item.key]
        item_entry.xor_item(item)

        # if entry is acked, delete it
        if item_entry.ack_hash == 0:
            del self.entry_at_key[item.key]
            del self.anchor_keys_for_item_key[item.key]


class Item:
    def __init__(self, acker, anchor=None, value=None):
        self.value = value
        self.key = random.getrandbits(160)
        self.acker = acker
        self.acker.register(self, anchor)
        if achor:
            self.add_anchor(anchor)

    def add_anchor(self, anchor):
        self.acker.add_anchor(self, anchor)

    def ack(self):
        if self.value is None:
            raise ValueError('Can only ack items whos value is not None')
        self.acker.ack(self)

##############################################################################
##############################################################################
##############################################################################
##############################################################################
#class State:
#    def __init__(self):
#        self._state = {}
#
#    def update(self, **kwargs):
#        for key, func in kwargs.items():
#            current_obj = self._state.get(key, None)
#            self._state[key] = func(current_obj)
#
#    def get(self, key):
#        return copy.deepcopy(self._state.get(key, None))
#
#
#
#def worker_func(item, state):
#    return item, state
#
#
#
#class Mapper(ProcessingNode):
#    async def process(self, item):
#        out_item = Item(anchor=item)
#        out_item.value = 1
#        await self.push(out_item)
#
#class Expander(ProcessingNode):
#    async def process(self, item):
#        out_list = []
#        for nn in range(10):
#            out_item = Item(anchor=item, value=1)
#            await self.push(out_item)
#
#class Reducer(ProcessingNode):
#    async def begin(self):
#        self.multi_anchor.clear()
#        await self.state.update(count=lambda: 0)
#
#    async def process(self, item):
#        await self.multi_anchor.add(item)
#        await self.state.update(count=lambda count: count + 1)
#
#    async def end(self):
#        out_item = Item(anchor=self.multi_anchor, value=self.state.get('count'))
#        self.push(out_item)
#
#





















