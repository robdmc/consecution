import sys
from consecution.nodes import GroupByNode


class GlobalState(object):
    """
    A simple class whos objects can absorb arbitrary user-defined attributes.
    """
    def __init__(self, **kwargs):
        for key, val in kwargs.items():
            self[key] = val

    def __str__(self):
        return 'GlobalState attributes: ' + str(sorted(vars(self).keys()))

    def __repr__(self):
        return self.__str__()

    def __setitem__(self, key, value):
        setattr(self, key, value)

    def __getitem__(self, key):
        return getattr(self, key)


class Pipeline(object):
    def __init__(self, node, global_state=None):
        # get a reference to the top node of the connected nodes supplied.
        self.top_node = node.top_node

        # set the pipeline global state
        if global_state:
            self.global_state = global_state
        else:
            self.global_state = GlobalState()

        # initialize an empty lookup for nodes
        self._node_lookup = {}

        # initialize the pipeline
        self.initialize()

    def initialize(self, with_push=False):
        # define a flag to determine if the pipeline is "running" or not
        # it will only be true between when the .begin() is run and the
        # .end() method is run.
        self._is_running = False
        self._needs_log_header = False

        # initialize each node
        for node in self.top_node.all_nodes:
            self.initialize_node(node, with_push)

        # build the pipeline repr by cycling through all the nodes
        self.top_node.top_down_make_repr()

        # print a logging header if any node is logging
        if self._needs_log_header:
            sys.stdout.write('node_log,what,node_name,item\n')

    def initialize_node(self, node, with_push=False):
        # give node reference to pipeline attributes
        node.pipeline = self
        node.global_state = self.global_state

        # make node available for lookup
        self._node_lookup[node.name] = node

        # set the _process callable to be either logged or unlogged
        # TODO: might want to change this logic so that groupby nodes
        # can be logged
        if isinstance(node, GroupByNode):
            node._process = node._process_item
        elif node._logging is None:
            node._process = node.process
        else:
            self._needs_log_header = True
            node._process = node._logged_process

        # for single downstreams with no logging, can short-circuit all logic
        # and directly wire up the downstream process() callable as the
        # push callable on this node
        short_it = len(node._downstream_nodes) == 1
        short_it = short_it and node._downstream_nodes[0]._logging is None
        short_it = short_it and not isinstance(
            node._downstream_nodes[0], GroupByNode)

        # only initialize push if requsted
        if with_push:
            if short_it and node._logging is None:
                node.push = node._downstream_nodes[0].process

            # logged or multiple downstreams require logic, so no short circuit
            else:
                node.push = node._push

    def __getitem__(self, name):
        node = self._node_lookup.get(name, None)
        if node is None:
            raise KeyError('\nNo node named {}'.format(name))
        return node

    def _pop_node_name(self, name, node_list):
        name_list = [n.name for n in node_list]
        if name in name_list:
            return node_list.pop(name_list.index(name))
        else:
            return None

    def __setitem__(self, name_to_replace, replacement_node):
        # make sure replacement node has proper name
        if name_to_replace != replacement_node.name:
            raise ValueError(
                '\nReplacement node must have the same name as the '
                'node it is replacing'
            )

        # this will automatically raise error if the name doesn't exist
        node_to_replace = self[name_to_replace]

        removals = []
        additions = []

        for upstream in node_to_replace._upstream_nodes:
            removals.append((upstream, node_to_replace))
            additions.append((upstream, replacement_node))
            # handle special case of upstream being a routing node
            if hasattr(upstream, '_end_point_map'):
                upstream._end_point_map[name_to_replace] = replacement_node

        for downstream in node_to_replace._downstream_nodes:
            removals.append((node_to_replace, downstream))
            additions.append((replacement_node, downstream))

        for upstream, downstream in removals:
            upstream.remove_downstream(downstream)

        for upstream, downstream in additions:
            upstream.add_downstream(downstream)

        # initialize the replacement node within the pipeline
        self.initialize_node(replacement_node)

        # if top node was replaced then make sure pipeline nows about it
        if replacement_node.name == self.top_node.name:
            self.top_node = replacement_node

    def __getattribute__(self, name):
        """
        This should trap for the begin() and end() method calls and install
        pre/post hooks for when they are called either on the pipeline
        class or on any class derived from it.
        """
        if name == 'begin':
            def wrapper():
                super(Pipeline, self).__getattribute__(name)()
                self._begin()
            return wrapper
        elif name == 'end':
            def wrapper():
                self._end()
                return super(Pipeline, self).__getattribute__(name)()
            return wrapper
        else:
            return super(Pipeline, self).__getattribute__(name)

    def begin(self):
        """
        Users can override these methods in derived classes.  They have
        no action here in base class, but the pre/post hooks are called
        to perform the necessary actions.
        """

    def end(self):
        """
        Users can override these methods in derived classes.  They have
        no action here in base class, but the pre/post hooks are called
        to perform the necessary actions.
        """

    def _begin(self):
        self.top_node.top_down_call('_begin')
        self.initialize(with_push=True)
        self._is_running = True

    def _end(self):
        self.top_node.top_down_call('end')
        self._is_running = False

    def push(self, item):
        if not self._is_running:
            self.begin()
        self.top_node._process(item)

    def consume(self, iterable):
        self.begin()
        for item in iterable:
            self.top_node._process(item)
        return self.end()

    def plot(self, file_name='pipeline', kind='png', notebook=False):
        self.top_node.plot(file_name, kind, notebook)

    def __str__(self):
        return (
            '\nPipeline\n'
            '----------------------------------'
            '----------------------------------\n{}'
            '----------------------------------'
            '----------------------------------\n'
        ).format(self._node_repr)

    def __repr__(self):
        return self.__str__()
