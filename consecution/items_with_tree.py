import random
from collections import defaultdict
from functools import partial

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

    def register(self, item, anchor_keys):
        # create an entry for the newly registered item
        self.entry_at_key[item.key] = AckerEntry(item)

        # assemble a list of all anchor keys for this item
        self.anchors_keys_for_item_key[item.key] = anchor_keys

        # xor this item with each of its anchors
        for anchor_key in anchor_keys:
            self.entry_at_key[anchor_key].xor_item(item)

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


#==============================================================================
#==============================================================================
#==============================================================================
#==============================================================================
#class MultiAnchor:
#    def __init__(self):
#        self.

class AckState:
    def __init__(self):
        self.all_acked = True

def xor_items(from_item, to_item):
    to_item.ack_hash = to_item.ack_hash ^ from_item.key

def ack(ack_state, from_item, to_item):
    xor_items(from_item, to_item)
    if ack_state.all_acked and from_item.ack_hash != 0:
        ack_state.all_acked = False


class Item:

    def __init__(self, value=None, anchor=None):
        self.value = value
        self.key = random.getrandbits(160)
        self.ack_hash = 0
        self.anchors = {anchor} if anchor else set([])
        self.upward_recursive_apply(partial(xor_items, self))

    def add_anchor(self, anchor):
        self.xor_item(self, anchor)
        self.anchors = self.anchors.add(anchor)

    def upward_recursive_apply(self, func, key_set=None):
        """
        recursively apply a function up the dependency graph
        func takes one argument:  func(item)
        """
        key_set = key_set if key_set else set([])
        if not self.key in key_set
            func(self)
            key_set.add(self.key)

        for anchor in self.anchors:
            key_set = anchor.upward_recursive_apply(func, key_set)

        return key_set

    def ack(self):
        ack_state = AckState()
        self.upward_recursive_apply(partial(xor_items, ack_state, self))
        return ack_state.all_acked




























