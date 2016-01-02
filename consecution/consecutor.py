from consecution.items import Item, Acker

#####################################################
In the node class, I need to find a good interface for writing
to different output channels.

Maybe:
    self.push_to_channel(channel, item)
    self.push_to_output(channel, item)
    self.write_to_output(channel, item)
    self.write_output(channel, item)
    self.output[channel].push(item)

#####################################################

class Consecutor:
    def __init__(self, input_node):
        self._input_iterable = []
        self._output_list_named = {}
        self.acker = Acker()
        input_node.apply_to_all_members(self._assign_consecutor_to_node)


    def _assign_consecutor_to_node(self, node):
        node.consecutor = self

    def _new_item(self, anchor=None, value=None):
        return Item(self.acker, anchor, value)

    def _run(self):
        #MAKE LOOP BE A LOCALIZED LOOP INSTEAD OF THE DEFAULT LOOP
        loop = asyncio.get_event_loop()

        #CALL THE RIGHT "STARTS" HERE FOR THE UNDERLYING LOOP
        loop.run_until_complete(self._start())

    def consume_from(self, iterable):
        self._input_iterable = iterable
        self.run()

    def push(self, value):
        self.consume_from([value])

    def get_output(self, name):







####################################################################
####################################################################
# It would be nice if the api to consecutors was all in the "sync" world
# hiding all the async stuff inside.
####################################################################
####################################################################


# will have to think about how timeouts play with output generators
cons1 = Consecutor(node1, timeout=time_delta_or_relative_delta)
cons2 = Consecutor(node2, output_spooled_to_disk=False)

cons1.consume(iterable, 'port1') # this blocks until all input is completely acked or timeout
cons1.push(value, 'port1') # this blocks until value is completely acked  or timeout


# acking is done once item is placed into output iterable
# generators are read-once.  They can only be gotten once.
gen = cons1.get_generator('port1')


# consecutor always has one port for iterating over unprocessed values
cons1.has_unprocessed # true/false
unprocessed_gen = cons1.get_generator('unprocessed')






