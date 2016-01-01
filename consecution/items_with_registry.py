import random
from collections import defaultdict

class AckerEntry:
    def __init__(self, item):
        self.ack_hash = item.key
        self.item = item

    def xor_item(self, item):
        self.ack_hash = self.ack_hash ^ item.key


class Acker:
    def __init__(self):
        self.entry_at_key = {}
        self.anchor_keys_for_item_key = defaultdict(set)

    def register(self, item, anchor=None):
        # create an entry for the newly registered item
        self.entry_at_key[item.key] = AckerEntry(item)

        if anchor:
            self.add_anchor(item, anchor)

    def add_anchor(self, item, anchor):
        self.anchor_keys_for_item_key[item.key].add(anchor.key)
        self.entry_at_key[anchor.key].xor_item(item)

    def ack(self, item):
        # ack this item for all its anchors
        anchor_keys_to_delete = []
        for anchor_key in self.anchor_keys_for_item_key[item.key]:
            anchor_entry = self.entry_at_key[anchor_key]
            anchor_entry.xor_item(item)
            # if entry is acked, delete it
            if anchor_entry.ack_hash == 0:
                anchor_keys_to_delete.append(anchor_key)

        # must run separate delete loop to avoid modifying dict over loop
        for anchor_key in anchor_keys_to_delete:
            del self.entry_at_key[anchor_key]
            del self.anchor_keys_for_item_key[anchor_key]


        # ack the current item by xor with itself
        item_entry = self.entry_at_key[item.key]
        item_entry.xor_item(item)


        # if entry is acked, delete it
        if item_entry.ack_hash == 0:
            del self.entry_at_key[item.key]
            del self.anchor_keys_for_item_key[item.key]

    def __str__(self):
        return (
            '============================================================\n'
            'acker with {} items\n'
            '{}\n{}\n\n'
        ).format(
            len(self.entry_at_key),
            self.entry_at_key,
            dict(self.anchor_keys_for_item_key)
        )
    def __repr__(self):
        return str(self)


class Item:
    def __init__(self, acker, anchor=None, value=None):
        self.value = value
        self.key = random.getrandbits(160)
        self.acker = acker
        self.acker.register(self, anchor)

    def add_anchor(self, anchor):
        self.acker.add_anchor(self, anchor)

    def ack(self):
        if self.value is None:
            raise ValueError('Can only ack items whos value is not None')
        self.acker.ack(self)

    def __str__(self):
        return str((self.value, self.key))


#if __name__ == '__main__':
#    acker = Acker()
#    print(acker)
#
#    i1 = Item(acker, value=1)
#    print(acker)
#    i2 = Item(acker, anchor=i1, value=2)
#    print(acker)
#
#    i3 = Item(acker, value=3)
#    i3.add_anchor(i1)
#    i3.add_anchor(i2)
#    print(acker)
#
#    i1.ack()
#    print(acker)
#    i2.ack()
#    print(acker)
#    i3.ack()
#    print(acker)

