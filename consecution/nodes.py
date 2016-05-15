class Node(object):
    def __init__(self, name):
        self.name = name
        self._upstream_nodes = []
        self._downstream_nodes = []

        # node network can be visualized with pydot.  These hold args and kwargs
        # that will be used to add and connect this node in the graph visualization
        self._pydot_node_kwargs = dict(name=self.name, shape='rectangle')
        self._pydot_edge_kwarg_list = []

    def __str__(self):
        return 'N({})'.format(self.name)

    def __repr__(self):
        return self.__str__()

    def __hash__(self):
        """
        define __hash__ method. dicts and sets will use this as key
        """
        return hash(id(self))

    def _validate_or_operator_args(self, other):
        # define a default error message
        default_msg = (
            '\n\nError connecting {} to {}.\n'
            'Only nodes or list of nodes or callables are allowed.'
        ).format(self, other)

        # nodes are okay
        if isinstance(other, Node):
            return

        # make sure input lists are valid
        if isinstance(other, list):
            # count the number of elements of each type
            num_callables, num_bad_kinds = 0, 0
            for el in other:
                if hasattr(el, '__call__'):
                    num_callables += 1
                elif not isinstance(el, Node):
                    num_bad_kinds += 1

            if num_bad_kinds > 0:
                raise ValueError(default_msg)

            if num_callables > 1:
                msg = (
                    '\n\nError connecting {} to {}.\n'
                    'Mutliple routing functions found.'
                ).format(self, other)

        # everything but a node or a list is an error
        else:
            raise ValueError(default_msg)

    def __or__(self, other):
        # make sure arguments are valid
        self._validate_or_operator_args(other)

        # convert all input to list form
        if isinstance(other, Node):
            other = [other]

        # need to snapshot current terminal set for returning later
        terminal_node_set = self.terminal_node_set

        # separate node elements from routing function elements
        downstream_nodes = [
            el for el in other if isinstance(el, Node)]
        routers = [
            el for el in other if hasattr(el, '__call__')]

        if routers:
            raise NotImplementedError('need to write this logic')
        else:
            self.connect_outputs(*downstream_nodes)

        ## if only one downstream node, then just connect it
        #if len(downstream_nodes) == 1:
        #    self.connect_outputs(*downstream_nodes)
        ## otherwise wire up a branching node
        #else:
        #    if routers:
        #        raise NotImplementedError('need to write this logic')
        #    else:
        #        self.connect_outputs(
        #    #branching_node = BranchingNode(name=self.name)
        #    #if routers:
        #    #    branching_node.set_routing_function(routers[0])
        #    #self.connect_outputs(branching_node)
        #    #branching_node.connect_outputs(*downstream_nodes)

        #out = list(self.terminal_node_set)
        out = list(terminal_node_set)
        return out[0] if len(out) == 1 else out




        #if routers:
        #    raise NotImplementedError('Need to finish routing code')
        #else:
        #    for downstream_node in downstream_nodes:
        #        self.add_downstream(downstream_node)

        #out = list(self.terminal_node_set)
        #return out[0] if len(out) == 1 else out

    def __ror__(self, other):
        """
        """
        if isinstance(other, Node):
            other = [other]

        #print '__ror__'
        #print 'self', self
        #print 'other', other

        self.connect_inputs(*other)
        out = list(self.terminal_node_set)

        # this is a useful debug line.  Don't delete it
        # print('{} | {} --> {}'.format(other, self, out))

        return out[0] if len(out) == 1 else out

    def validate_inputs(self, upstreams):
        if len(upstreams) == 0:
            msg = (
                'Error connecting {} to {}.\n'
                'There must be at least one node to connect to.'
            ).format(upstreams, self)
            raise ValueError(msg)

        if len(self.initial_node_set) > 1 and len(upstreams) > 1:
            msg = (
                'Error connecting {} to {}.\n'
                'Many-to-many connections are not permitted'
            ).format(upstreams, self)
            raise ValueError(msg)
        #TODO:  Need to bring this over
        #self._detect_cycles(upstreams, self.downstream_set)

    def connect_inputs(self, *upstreams):
        """
        Logic for connecting sub-graphs
        """
        self.validate_inputs(upstreams)

        # need to use snapshot of initial_node_set because loop updates it
        initial_node_set = self.initial_node_set

        for upstream in upstreams:
            for input_node in initial_node_set:
                upstream.add_downstream(input_node)

    def validate_outputs(self, downstreams):
        if len(downstreams) == 0:
            msg = (
                'Error connecting {} to {}.\n'
                'There must be at least one node to connect to.'
            ).format(self, downstreams)
            raise ValueError(msg)

        if len(self.terminal_node_set) > 1 and len(downstreams) > 1:
            msg = (
                'Error connecting {} to {}.\n'
                'Many-to-many connections are not permitted'
            ).format(self, downstreams)
            raise ValueError(msg)
        #TODO bring this over too
        #self._detect_cycles(self.upstream_set, downstreams)

    def connect_outputs(self, *downstreams):
        downstreams = list(downstreams)
        self.validate_outputs(downstreams)
        terminal_node_set = self.terminal_node_set
        for term_node in terminal_node_set:
            for downstream in downstreams:
                term_node.add_downstream(downstream)

    def _detect_cycles(self, upstreams, downstreams):
        downstream_set = set()
        upstream_set = set()

        for downstream in downstreams:
            downstream_set = downstream_set.union(
                set(downstream.depth_first_search('down'))
            )

        for upstream in upstreams:
            upstream_set = upstream_set.union(
                set(upstream.depth_first_search('up'))
            )


        common_nodes = downstream_set.intersection(upstream_set)

        if common_nodes:
            msg = (
                '\n\nLoop detected in pipeline graph.'
                '  Node(s) {} encountered twice.'
            ).format(common_nodes)
            raise ValueError(msg)

    @property
    def top_node(self):
        """
        Use a stack to emulate recursive search for top node.
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
        Find all terminal nodes rooted in this node
        """
        return {
            node for node in self.depth_first_search('down')
            if len(node._downstream_nodes) == 0
        }

    @property
    def initial_node_set(self):
        """
        Find all initial nodes rooted at this node
        """
        self.depth_first_search('up')
        return {
            node for node in self.depth_first_search('up')
            if len(node._upstream_nodes) == 0
        }


    @property
    def root_nodes(self):
        """
        Find root nodes of entire connected network
        """
        print
        print 'lookin for root'
        for node in  sorted(self.all_nodes):
            print node.name, node._upstream_nodes
        print
        return [
            node for node in self.all_nodes
            if len(node._upstream_nodes) == 0
        ]

    @property
    def all_nodes(self):
        return self.depth_first_search('both')

    def depth_first_search(self, direction='both'):
        """
        This is a depth first search using a stack to emulate recursion
        see good explanation at
        https://jeremykun.com/2013/01/22/depth-and-breadth-first-search/
        """
        # holds all nodes that have been visited
        visited_nodes = set()

        # holds nodes that still need to be explored
        stack = [self]

        # while I still have nodes that need exploring
        while len(stack) > 0:
            # get the next node to explore
            node = stack.pop()

            # if I've already seen this node, nothing to do, so go to next
            if node in visited_nodes:
                continue

            # Make sure I don't visit this node again
            visited_nodes.add(node)

            if direction == 'up':
                neighbors = node._upstream_nodes
            elif direction == 'down':
                neighbors = node._downstream_nodes
            elif direction == 'both':
                neighbors = node._upstream_nodes + node._downstream_nodes
            else:
                raise ValueError(
                    'direction must be \'up\', \'dowwn\' or \'both\'')

            # search all neightbors to this node for unvisited nodes
            for node in neighbors:
                # if you find unvisited node, add it to nodes needing visit
                if node not in visited_nodes:
                    stack.append(node)

        # should have hit all nodes in the graph at this point
        return visited_nodes

    def _validate_node(self, other):
        # only nodes allowed to be connected
        if not isinstance(other, Node):
            raise ValueError('Trying to connect a non-node type')

        # a duplicate is a node with same name, but different hash
        hash_for_name = {n.name: hash(n) for n in self.all_nodes}
        if other.name in hash_for_name:
            if hash(other) != hash_for_name[other.name]:
                raise ValueError('A Node nameed \'{}\' already exists'.format(
                    other.name))

    def add_downstream(self, other):
        self._validate_node(other)
        self._downstream_nodes.append(other)
        other._upstream_nodes.append(self)

        self._pydot_edge_kwarg_list.append(
            dict(src=self.name, dst=other.name, dir='forward'))

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
        import pydot

        # create a pydot graph
        graph = pydot.Dot(graph_type='graph')

        # create pydot nodes for every node connected to this one
        for node_kwargs in node_kwargs_list:
            graph.add_node(pydot.Node(**node_kwargs))

        # creat pydot edges between all nodes connected to this one
        for edge_kwargs in edge_kwargs_list:
            graph.add_edge(pydot.Edge(**edge_kwargs))

        return graph

    def draw_graph(
            self, file_name='pipeline', kind='png', display_noteook=False):  # pragma: no cover  (see above for why)
        """
        This method draws a pydot graph of your processing tree.  It does so using the
        pydot library which is based on the graphviz library.  You should only ever need
        to do this for developement/debug, so the configuration required to do this is not
        needed in production.  Since it doesn't make sense to call this method in production,
        the imports it requires are loaded within the method itself.  That way we only
        need the dependencies on a dev machine.  Pydot is a bit finicky about versioning, so
        this is what works as of  3/25/16.
        MacOS
          conda uninstall pydot
          brew install graphviz
          pip install pydot2
          pip install pyparsing==1.5.7

        file_name: [str] the name of the visualization file
        kind: [str] the type of visualization file to create
        display_notebook: [bool]  Automatically load up the visualization in IPython Notebook
        """
        graph = self._build_pydot_graph()

        # define allowed formats for saving the graph visualization
        ALLOWED_KINDS = {'pdf', 'png'}
        if kind not in ALLOWED_KINDS:
            raise ValueError('Only the following kinds are supported: {}'.format(ALLOWED_KINDS))

        # make sure supplied filenames have the write extension
        if file_name[-4:] != '.' + kind:
            file_name = '{}.{}'.format(file_name, kind)

        #graph.write_raw('rob.dot')
        # write the appropriate file
        if kind == 'pdf':
            graph.write_pdf(file_name)
        elif kind == 'png':
            graph.write_png(file_name)

        # display to notebook if requested
        if display_noteook:
            # do import here because IPython not core dependancy
            from IPython.display import Image, display
            graph.write_png(file_name)
            display(Image(filename=file_name))


