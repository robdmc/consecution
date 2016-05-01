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
            return root_nodes[0]

    @property
    def root_nodes(self):
        return [
            node for node in self.all_nodes
            if len(node._upstream_nodes) == 0
        ]

    @property
    def all_nodes(self):
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

            # search all neightbors to this node for unvisited nodes
            for node in node._upstream_nodes + node._downstream_nodes:
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


