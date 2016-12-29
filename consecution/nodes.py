import sys
from collections import Counter, deque, OrderedDict
import traceback
from consecution.utils import Clock


class Node(object):
    """
    :type name: str
    :param str: The name of this node.  Must be unique within a pipeline.

    :type kwargs:  keyword args
    :param kwargs: Any additional keyword args are assigned as attributes
                   on the node.

    You create nodes by inheriting from this class.  You will be required to
    implement a `.process()` on your class.  You can call the `.push()` method
    from anywhere in your class implementation except from within the
    `.begin()` method.

    Note that although this documentation refers to "the `.push` method",
    `push` is actually  a callable attribute assigned when nodes are placed
    into pipelines.

    Its signature is `.push(item)`, where `item` can be anything you want pushed
    to nodes connected to the downstream side of the node.

    """
    def __init__(self, name, **kwargs):
        # assign any user-defined attributes
        for k, v in kwargs.items():
            setattr(self, k, v)
        self.name = name
        self._upstream_nodes = []
        self._downstream_nodes = []

        self._num_top_down_calls = 0

        # node network can be visualized with pydot.  These hold args and kwargs
        # that will be used to add and connect this node in the graph visualization
        self._pydot_node_kwargs = dict(name=self.name, shape='rectangle')
        self._pydot_edge_kwarg_list = []

        self._router = None

        # this will be one of three values: None, 'input', 'output'
        self._logging = None

        # add a clock to allow for timing
        self.clock = Clock()

    def __str__(self):
        return 'N({})'.format(self.name)

    def __repr__(self):
        return self.__str__()

    def __hash__(self):
        """
        define __hash__ method. dicts and sets will use this as key
        """
        return id(self)

    def __eq__(self, other):
        return self.__hash__() == other.__hash__()

    def __lt__(self, other):
        """
        I need this to be able to sort by name
        """
        return self.name < other.name

    def __getitem__(self, key):
        msg = (
            '\n\nYou cannot call __getitem__ on nodes.  You tried to call\n'
            '{self} [{key}]\n'
            'which doesn\'t make sense.  You probably meant\n'
            '{self} | [{key}]\n'
        ).format(self=self, key=key)
        raise ValueError(msg)

    def _get_flattened_list(self, obj):
        if isinstance(obj, Node):
            return [obj]

        elif hasattr(obj, '__iter__'):
            nodes = []
            for el in obj:
                if isinstance(el, Node):
                    nodes.append(el)
                elif hasattr(el, '__iter__'):
                    nodes.extend(self._get_flattened_list(el))
            return nodes
        else:
            msg = (
                'Don\'t know what to do with {}.  It\'s not a node, and it\'s '
                'not iterable.'
            ).format(repr(obj))
            raise ValueError(msg)

    def _get_exposed_slots(self, obj, pointing):
        nodes = set()
        for node in self._get_flattened_list(obj):
            if pointing == 'left':
                nodes = nodes.union(node.initial_node_set)
            elif pointing == 'right':
                nodes = nodes.union(node.terminal_node_set)
            else:
                raise ValueError('pointing must be "left" or "right"')
        return nodes

    def _connect_lefts_to_rights(self, lefts, rights, router=None):
        slots_from_left = self._get_exposed_slots(lefts, pointing='right')
        slots_from_right = self._get_exposed_slots(rights, pointing='left')
        for left in slots_from_left:
            router_node = None
            if router:
                router_name = '{}.{}'.format(
                    left.name, self._get_object_name(router))
                end_point_map = {n.name: n for n in slots_from_right}
                router_node = _RouterNode(
                    router_name, end_point_map, router)
                left.add_downstream(router_node)
            for right in slots_from_right:
                if router_node:
                    router_node.add_downstream(right)
                else:
                    left.add_downstream(right)

    def _get_object_name(self, obj):
        class_name = obj.__class__.__name__
        if class_name == 'function':
            return obj.__name__
        else:
            return class_name

    def _get_router(self, obj):
        router = None
        if hasattr(obj, '__iter__'):
            routers = [el for el in obj if hasattr(el, '__call__')]
            router = routers[0] if routers else None
        return router

    def __or__(self, other):
        router = self._get_router(other)
        self._connect_lefts_to_rights(self, other, router)
        return self

    def __ror__(self, other):
        self._connect_lefts_to_rights(other, self)
        return self

    @property
    def top_node(self):
        """
        This attribute always holds the top-most node in the node graph.
        Consecution only allows one top node.
        """
        root_nodes = self.root_nodes
        if len(root_nodes) > 1:
            msg = 'You must remove one of the following input nodes {}'.format(
                root_nodes)
            raise ValueError(msg)
        else:
            return root_nodes.pop()

    @property
    def terminal_node_set(self):
        """
        This attribute holds a set of all bottom nodes in the node graph.
        """
        return {
            node for node in self.depth_first_walk('down')
            if len(node._downstream_nodes) == 0
        }

    @property
    def initial_node_set(self):
        """
        When piecing together fragments of a graph, you can temporarily have
        connected nodes with multiple "top-nodes."  This method returns this
        set of nodes.  Node that consecution can only make pipelines from
        graphs having a single top node.
        """
        self.depth_first_walk('up')
        return {
            node for node in self.depth_first_walk('up')
            if len(node._upstream_nodes) == 0
        }

    @property
    def root_nodes(self):
        """
        This attribute holds a list of all nodes that do not have any upstream
        nodes attached.
        """
        return [
            node for node in self.all_nodes
            if len(node._upstream_nodes) == 0
        ]

    @property
    def all_nodes(self):
        """
        This attribute contains a set of all nodes in the graph.
        """
        return self.depth_first_walk('both')

    def log(self, what):
        """
        Calling this method on a node will turn on its logging feature.  This
        means that the node will print logged items to the console.  You can
        choose whether to log the inputs or outputs of a node.

        :type name: what
        :param what: One of 'input' or 'output' indicating whther you want to
                     log the input or output of this node.
        """
        allowed = ['input', 'output']
        if what not in allowed:
            raise ValueError(
                '\'what\' argument must be in {}'.format(allowed)
            )
        self._logging = what

    def _get_downstream_reps(self):
        if self._downstream_nodes:
            downstreams = sorted([n.name for n in self._downstream_nodes])

            if len(downstreams) == 1:
                downstreams = downstreams[0]

            template = '{{: >{}s}} | {{}}\n'.format(
                self.pipeline._longest_node_name_len_)

            self.pipeline._node_repr += template.format(
                self.name, downstreams).replace('\'', '')

    def top_down_make_repr(self):
        """
        You should never need to use this method.  It iterates through the node
        graph in top-down order making a repr string for each node.
        """
        if not hasattr(self, 'pipeline'):
            raise ValueError(
                'top_down_make_repr can only be called for nodes in a pipeline')

        self.pipeline._longest_node_name_len_ = max(
            len(n.name) for n in self.all_nodes)
        self.pipeline._node_repr = ''
        self.top_node.top_down_call('_get_downstream_reps')

    def top_down_call(self, method_name):
        """
        This utility method traverses the graph in top-down order and invokes
        the named method on every node it encounters. It is used internally
        to make sure the `.begin()` and `.end()` methods are not called before
        their upstream counterparts.

        :type method_name: str
        :param method_name: The name of the method you would like to call in
                            top-down order.
        """
        # record the number of upstreams this node has
        num_upstreams = len(self._upstream_nodes)

        # if this node isn't pulling from multiple upstreams, it's ready
        # to recurse to downstreams
        if num_upstreams <= 1:
            ready_for_downstreams = True
        # this node isn't ready to recurse to downstreams until the current
        # call would mean the last required call.
        elif self._num_top_down_calls == num_upstreams - 1:
            ready_for_downstreams = True
        else:
            ready_for_downstreams = False

        # if ready to recurse, then call the method on self and recurse
        # downwards.
        if ready_for_downstreams:
            getattr(self, method_name)()
            for downstream in self._downstream_nodes:
                downstream.top_down_call(method_name)
            self._num_top_down_calls = 0
        else:
            self._num_top_down_calls += 1

    def depth_first_walk(self, direction='both', as_ordered_list=False):
        """
        This method walks the graph of connected nodes in depth-first
        order.  It uses a stack to emulate recursion. See good explanation at
        https://jeremykun.com/2013/01/22/depth-and-breadth-first-search/

        :type direction: str
        :param direction: one of 'up', 'down' or 'both' specifying the direction
                          to walk.
        :type as_ordered_list: Bool
        :param as_ordered_list: If set to true, returns the walked nodes as
                                an ordered list instead of an unordered set.

        :rtype: list or set
        :return: An iterable of the discovered nodes.
        """
        return self.walk(
            direction=direction, how='depth_first',
            as_ordered_list=as_ordered_list)

    def breadth_first_walk(self, direction='both', as_ordered_list=False):
        """
        This method walks the graph of connected nodes in breadth-first
        order.  It uses a stack to emulate recursion. See good explanation at
        https://jeremykun.com/2013/01/22/depth-and-breadth-first-search/

        :type direction: str
        :param direction: one of 'up', 'down' or 'both' specifying the direction
                          to walk.
        :type as_ordered_list: Bool
        :param as_ordered_list: If set to true, returns the walked nodes as
                                an ordered list instead of an unordered set.

        :rtype: list or set
        :return: An iterable of the discovered nodes.
        """
        return self.walk(
            direction=direction, how='breadth_first',
            as_ordered_list=as_ordered_list)

    def walk(
            self, direction='both', how='breadth_first', as_ordered_list=False):

        """
        This is the core algorithm for walking a graph in specified order.  It
        is used by the `breadth_first_walk` and `depth_first_walk` methods.

        :type how: str
        :param how: one of 'breadth_first' or 'depth_first'

        :type direction: str
        :param direction: one of 'up', 'down' or 'both' specifying the direction
                          to walk.
        :type as_ordered_list: Bool
        :param as_ordered_list: If set to true, returns the walked nodes as
                                an ordered list instead of an unordered set.

        :rtype: list or set
        :return: An iterable of the discovered nodes.
        """
        if how not in {'depth_first', 'breadth_first'}:
            raise ValueError(
                '\'how\' argument must be one of '
                '[\'depth_first\', \'breadth_first\']'
            )
        # What I really want is an ordered set, which doesn't exist.  So I'm
        # using the keys of an ordered dict to get the functionality I want.
        # I have no need for the values in this dict, only the keys.
        visited_nodes = OrderedDict()

        # holds nodes that still need to be explored
        queue = deque([self])

        # while I still have nodes that need exploring
        while len(queue) > 0:
            # get the next node to explore
            node = queue.pop()

            # if I've already seen this node, nothing to do, so go to next
            if node in visited_nodes:
                continue

            # Make sure I don't visit this node again
            # again.  I'm using an ordered dict to mimic an ordered set.
            # I have no need for the value, so set it to None
            visited_nodes[node] = None

            neighbor_dict = {
                'up': node._upstream_nodes,
                'down': node._downstream_nodes,
                'both': node._upstream_nodes + node._downstream_nodes,
            }
            if direction not in neighbor_dict:
                raise ValueError(
                    'direction must be \'up\', \'dowwn\' or \'both\'')
            neighbors = neighbor_dict[direction]

            # search all neightbors to this node for unvisited nodes
            for node in neighbors:
                # if you find unvisited node, add it to nodes needing visit
                if node not in visited_nodes:
                    if how == 'breadth_first':
                        queue.appendleft(node)
                    else:
                        queue.append(node)

        # should have hit all nodes in the graph at this point
        if as_ordered_list:
            return list(visited_nodes.keys())
        else:
            return set(visited_nodes.keys())

    def _check_for_dups(self):
        counter = Counter()
        for node in self.all_nodes:
            counter.update({node.name: 1})
        dups = [name for (name, count) in counter.items() if count > 1]
        if dups:
            msg = (
                '\n\nNode names must be unique.  Dupicates {} found.'
            ).format(list(dups))
            raise ValueError(msg)
        return

    def _check_for_cycles(self):
        self_and_upstreams = self.depth_first_walk('up')
        downstreams = self.depth_first_walk('down') - {self}
        common_nodes = self_and_upstreams.intersection(downstreams)
        if common_nodes:
            raise ValueError('\n\nYour graph is not acyclic.  It has loops.')

    def _validate_node(self, other):
        # only nodes allowed to be connected
        if not isinstance(other, Node):
            raise ValueError('Trying to connect a non-node type')

    def add_downstream(self, other):
        """
        You will probably use this method quite a bit.  It is used to manually
        attach a downstream node.

        :type other: consecution.Node
        :param other: An instance of the node you want to attach
        """
        self._validate_node(other)
        self._downstream_nodes.append(other)
        other._upstream_nodes.append(self)

        self._check_for_dups()
        if self.name == other.name:
            raise ValueError('{} can\'t be downstream to itself'.format(self))
        self._check_for_cycles()

        self._pydot_edge_kwarg_list.append(
            dict(tail_name=self.name, head_name=other.name))

    def remove_downstream(self, other):
        """
        This method removes the given node from being attached as a downstream
        node.

        :type other: consecution.Node
        :param other: An instance of the node you want to remove
        """
        # remove self from the other's upstreams
        other._upstream_nodes = [
            n for n in other._upstream_nodes if n.name != self.name]

        # remove other from self's downstream nodes
        self._downstream_nodes = [
            n for n in self._downstream_nodes if n.name != other.name]

        # remove this connection from the pydot kwargs list
        new_kwargs_list = []
        for kwargs in self._pydot_edge_kwarg_list:
            if kwargs['head_name'] == other.name:
                continue
            new_kwargs_list.append(kwargs)
        self._pydot_edge_kwarg_list = new_kwargs_list

    def _build_pydot_graph(self):
        """
        This private method builds a pydot graph
        """
        # define kwargs lists for creating the visualization (these are closure vars for function below)
        node_kwargs_list, edge_kwargs_list = [], []

        # define a function to map over all nodes to aggreate viz kwargs
        def collect_kwargs(node):
            node_kwargs_list.append(node._pydot_node_kwargs)
            edge_kwargs_list.extend(node._pydot_edge_kwarg_list)

        for node in self.all_nodes:
            collect_kwargs(node)

        # doing import inside method so that pydot dependency is optional
        from graphviz import Digraph

        # create a pydot graph
        graph = Digraph(comment='pipeline')

        # create pydot nodes for every node connected to this one
        for node_kwargs in node_kwargs_list:
            graph.node(**node_kwargs)

        # creat pydot edges between all nodes connected to this one
        for edge_kwargs in edge_kwargs_list:
            graph.edge(**edge_kwargs)

        return graph

    def plot(
            self, file_name='pipeline', kind='png'):
        """
        This method draws a visualization of your processing graph.  You must
        have graphviz installed on your system for it to work properly.  (See
        install instructions.)

        If you are running consecution in an Jupyter notebook, you can display
        an inline visualization of a pipeline by simply making the pipeline be
        the final expression in a cell.

        :type file_name: str
        :param file_name: The name of the image file to generate

        :type kind: str
        :param kind: The kind of file to generate (png, pdf)
        """
        graph = self._build_pydot_graph()

        # define allowed formats for saving the graph visualization
        ALLOWED_KINDS = {'pdf', 'png'}
        if kind not in ALLOWED_KINDS:
            raise ValueError('Only the following kinds are supported: {}'.format(ALLOWED_KINDS))

        # set the output format
        graph.format = kind

        file_name = file_name.replace('.{}'.format(kind), '')

        # write the output file
        try:
            graph.render(file_name)
        except RuntimeError:
            sys.stderr.write(
                '\n\n'
                '=========================================================\n'
                'Problem executing GraphViz.  Make sure you have it\n'
                'properly installed.\n'
                'http://www.graphviz.org/\n'
                'If you are on a mac, you should be able to install it with\n'
                'brew install graphviz.\n\n'
                'If you are on ubuntu, you can install it with\n'
                'apt-get install graphviz\n'
                '=========================================================\n'
                '\n\n'
            )
            raise

    def process(self, item):
        """
        :type item: object
        :param item: The item this node should process

        You must override this method with your own logic.
        """
        raise NotImplementedError(
            (
                'Error in node named {}\n'
                'You must define a .process(self, item) method on all nodes'
            ).format(repr(self.name))
        )

    def reset(self):
        """
        User can override this to do whatever logic they want.
        """

    def _logged_process(self, item):
        if self._logging == 'input':
            self._write_log(item)
        self.process(item)

    def _begin(self):
        try:
            self.begin()
        except AttributeError:
            e = sys.exc_info()[1]
            tb = sys.exc_info()[2]
            (
                code_file, line_no, method_name, line_txt
            ) = traceback.extract_tb(tb)[-1]
            msg = str(e) + (
                '\n\nError in .begin() method of \'{}\' node.\n'
                'Are you trying to call .push() from inside the\n'
                '.begin() method?  That is not allowed.\n\n'
                'file: {}, line{}\n--> {}\n\n'
            ).format(self.name, code_file, line_no, line_txt)
            traceback.print_exc()
            raise AttributeError(msg)

    def begin(self):
        pass

    def end(self):
        pass

    def _write_log(self, item):
        sys.stdout.write('node_log,{},{},{}\n'.format(self._logging, self.name, item))

    def _push(self, item):
        """
        This is the default pusher.  It pushes to all downstreams.
        """
        if self._logging == 'output':
            self._write_log(item)

        # The _process attribute will be set to the appropriate callable
        # when initializing the pipeline.  I do this because I want the
        # chaining to be as efficient as possible.  If logging is not set,
        # I don't want to have to hit that logic every push, so I just
        # invoke a callable attribute at each process that has been set
        # to the appropriate callable.
        for downstream in self._downstream_nodes:
            downstream._process(item)


class _RouterNode(Node):
    """
    This node will route to downstreams.  The router function needs to
    return the name of the destination node.
    """
    def __init__(self, name, end_point_map, route_callable):
        super(_RouterNode, self).__init__(name)
        self._end_point_map = end_point_map
        self._pydot_node_kwargs = dict(name=self.name, shape='oval')
        self._route_callable = route_callable

    def process(self, item):
        """
        This is the default pusher.  It pushes to all downstreams.
        """
        node = self._end_point_map.get(self._route_callable(item), None)
        if node is None:
            raise ValueError(
                (
                    '\n\nRouter node {} encountered bad route path {}.  Valid '
                    'route paths are {}.'
                ).format(
                    self.name,
                    repr(self._route_callable(item)),
                    [n.name for n in self._downstream_nodes]
                )
            )

        node._process(item)


class GroupByNode(Node):
    def __init__(self, *args, **kwargs):
        super(GroupByNode, self).__init__(*args, **kwargs)
        self._batch_ = []
        self._previous_key = '__no_previous_key__'

    def key(self, item):
        """
        You must define this method.

        :type item: object
        :param item: The item you are processing

        :rtype: hashable object
        :return: a hashable object that serves as a key for the grouping process
        """
        raise NotImplementedError(
            'you must define a .key(self, item) method on all '
            'GroupBy nodes.'
        )

    def process(self, batch):
        """
        You must define this method.

        :type batch: iterable
        :param batch: A batch of items having the same key
        """
        raise NotImplementedError(
            'You must define a .process(self, batch) method on all GroupBy '
            'nodes.'
        )

    def _process_item(self, item):
        key = self.key(item)
        if key != self._previous_key:
            self._previous_key = key
            if len(self._batch_) > 0:
                self.process(self._batch_)
            self._batch_ = [item]
        else:
            self._batch_.append(item)

    def _end(self):
        self.process(self._batch_)
        self._batch_ = []

    def __getattribute__(self, name):
        """
        This should trap for the end() method calls and install
        pre hook.
        """
        if name == 'end':
            def wrapper():
                self._end()
                return super(GroupByNode, self).__getattribute__(name)()
            return wrapper
        else:
            return super(GroupByNode, self).__getattribute__(name)
