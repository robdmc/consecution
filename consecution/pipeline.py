import sys
from consecution.nodes import GroupByNode


class GlobalState(object):
    """
    GlobalState is a simple container class that sets its attributes from
    constructor kwargs.  It supports both object and dictionary access to its
    attributes.  So, for example, all of the following statements are supported.

    .. code-block:: python

       from consecution import GlobalState

       global_state = GlobalState(a=1, b=2)
       global_state['c'] = 2
       a = global_state['a']

    An object of this class will be created as the default ``.global_state``
    attribute on a Pipeline if you do not explicitely provide a global_state
    argument to the constructor.
    """
    # I'm using unconventional "_item_self_" name here to avoid
    # conflicts when kwargs actually contain a "self" arg.

    def __init__(_item_self, **kwargs):
        for key, val in kwargs.items():
            _item_self[key] = val

    def __str__(_item_self):
        quoted_keys = [
            '\'{}\''.format(k) for k in sorted(vars(_item_self).keys())]
        att_string = ', '.join(quoted_keys)
        return 'GlobalState({})'.format(att_string)

    def __repr__(_item_self):
        return _item_self.__str__()

    def __setitem__(_item_self, key, value):
        setattr(_item_self, key, value)

    def __getitem__(_item_self, key):
        return getattr(_item_self, key)


class Pipeline(object):
    """
    :type node: Node
    :param node: Any node in a connected graph

    :type global_state:  object
    :param global_state: Any python object you want to use for holding global
                         state.

    Once Nodes have been wired together, they must be placed in a pipeline in
    order to process data.  If you would like to peform pipeline-level set up and
    tear-down logic, you can subclass from Pipeline and override the
    ``.begin()`` and ``end()`` methods.
    """
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
            raise KeyError('No node named \'{}\''.format(name))
        return node

    def __setitem__(self, name_to_replace, replacement_node):
        # make sure replacement node has proper name
        if name_to_replace != replacement_node.name:
            raise ValueError(
                'Replacement node must have the same name.'
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
        elif name == 'reset':
            def wrapper():
                self._reset()
                return super(Pipeline, self).__getattribute__(name)()
            return wrapper
        else:
            return super(Pipeline, self).__getattribute__(name)

    def begin(self):
        """
        Override this method to execute any logic you want to perform before
        setting up nodes.  The ``.begin()`` method of all nodes will be called.
        """

    def end(self):
        """
        Override this method to execute any logic you want to perform after
        all nodes are done processing data. The ``.end()`` method of all nodes
        will be called.
        """

    def reset(self):
        """
        Override this with any logic you'd like to perform for resetting the
        pipeline. The ``.reset()`` method of all nodes will be called.
        """

    def _reset(self):
        self.top_node.top_down_call('reset')

    def _begin(self):
        self.top_node.top_down_call('_begin')
        self.initialize(with_push=True)
        self._is_running = True

    def _end(self):
        self.top_node.top_down_call('end')
        self._is_running = False

    def push(self, item):
        """
        You can manually push items to your pipeline using this meethod.

        :type item: object
        :param item: Any object you would like the pipeline to process
        """
        if not self._is_running:
            self.begin()
        self.top_node._process(item)

    def consume(self, iterable):
        """
        The pipeline will process each item in the iterable.

        :type iterable: A Python Iterable
        :param iterable: An iterable of objects you would like to process
        """
        self.begin()
        for item in iterable:
            self.top_node._process(item)
        return self.end()

    def plot(self, file_name='pipeline', kind='png'):
        """
        Call this method to produce a visualization of your pipeline.  The
        Graphviz library will be used to generate the image file.  Note that
        pipelines are automatically visualized in IPython notebook when they are
        evaluated as the last expression in a cell.

        :type file_name: str
        :param file_name: The name of the image file to save

        :type kind: str
        :param kind: The type of image file to produce (png, pdf)
        """
        self.top_node.plot(file_name, kind)
        return self

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

    # No good way to test this unless you know dot is installed.
    def _repr_svg_(self):  # pragma: no cover
        return self.top_node._build_pydot_graph()._repr_svg_()
