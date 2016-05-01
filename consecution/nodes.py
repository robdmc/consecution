class Node(object):
    def __init__(self, name):
        self.name = name
        self._upstream_nodes = []
        self._downstream_nodes = []

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
