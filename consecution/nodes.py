
class Node(object):
    def __init__(self, name):
        self.name = name
        self._upstream_nodes = []
        self._downstream_nodes = []

    def __str__(self):
        return 'N({})'.format(self.name)

    def __repr__(self):
        return self.__string__()

    #@property
    #def top_node(self):
    #    if self._upstream_nodes:
    #        return self._upstream_nodes[0].top_node
    #    else:
    #        return self

    @property
    def top_node(self):
        """
        Use a stack to emulate recursive search for top node.
        """
        root_nodes = self.root_nodes
        if len(root_list) > 1:
            raise ValueError('Your pipeline must have only one input node')
        else:
            return root_nodes[0]

    #@property
    #def _self_and_downstreams(self):
    #    out = set(self)
    #    for downstream in self._downstream_nodes:
    #        for further_downstream in downstream._self_and_downstreams:
    #            out.add(further_downstream)
    #    return list(out)

    @property
    def root_nodes(self)
        return [
            node for node in self.all_nodes
            if len(node._upstream_nodes) == 0)
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

        # no duplicate names allowed
        existing_names = {n.name for n in self.all_nodes}
        if other.name in existing_names:
            raise ValueError('A Node nameed \'{}\' already exists'.format(
                other.name))


    def add_downstream(self, other):
        self._validate_node(other)
        self._downstream_nodes.append(other)
        other._upstream_nodes.append(self)


    #def depth_first_search(starting_node, sought_value):
    #    # see good explanation for depth_first_search
    #    # https://jeremykun.com/2013/01/22/depth-and-breadth-first-search/

    #    # holds all nodes that have been visited
    #    visited_nodes = set()

    #    # holds nodes that still need to be explored
    #    stack = [starting_node]

    #    # while I still have nodes that need exploring
    #    while len(stack) > 0:
    #        # get the next node to explore
    #        node = stack.pop()

    #        # if I've already seen this node, nothing to do, so go to next
    #        if node in visited_nodes:
    #            continue

    #        # Make sure I don't visit this node again
    #        visited_nodes.add(node)

    #        # do search logic  (will have to change this
    #        if node.value == sought_value:
    #            return True

    #        # search all neightbors to this node for unvisited nodes
    #        for n in node.adjacent_nodes:
    #            # if you find an unvisited node, add it to nodes you need to
    #            # visit
    #            if n not in visited_nodes:
    #                stack.append(n)
    #    return False




#def depth_first_search(starting_node, sought_value):
#    # see good explanation for depth_first_search
#    # https://jeremykun.com/2013/01/22/depth-and-breadth-first-search/
#
#    # holds all nodes that have been visited
#    visited_nodes = set()
#
#    # holds nodes that still need to be explored
#    stack = [starting_node]
#
#    # while I still have nodes that need exploring
#    while len(stack) > 0:
#        # get the next node to explore
#        node = stack.pop()
#
#        # if I've already seen this node, nothing to do, so go to next
#        if node in visited_nodes:
#            continue
#
#        # Make sure I don't visit this node again
#        visited_nodes.add(node)
#
#        # do search logic  (will have to change this
#        if node.value == sought_value:
#            return True
#
#        # search all neightbors to this node for unvisited nodes
#        for n in node.adjacent_nodes:
#            # if you find an unvisited node, add it to nodes you need to
#            # visit
#            if n not in visited_nodes:
#                stack.append(n)
#    return False





    #def depth_first_search(self, direction='both'):
    #    """
    #    This is a depth first search using a stack to emulate recursion
    #    see good explanation at
    #    https://jeremykun.com/2013/01/22/depth-and-breadth-first-search/
    #    """
    #    allowed_directions = {'up', 'down', 'both'}
    #    if direction not in allowed_directions:
    #        raise ValueError('direction nmust be one of {}'.format(
    #            allowed_directions))


    #    # holds all nodes that have been visited
    #    visited_nodes = set()

    #    # holds nodes that still need to be explored
    #    stack = [self]

    #    # while I still have nodes that need exploring
    #    while len(stack) > 0:
    #        # get the next node to explore
    #        node = stack.pop()

    #        # if I've already seen this node, nothing to do, so go to next
    #        if node in visited_nodes:
    #            continue

    #        # Make sure I don't visit this node again
    #        visited_nodes.add(node)

    #        # determine adjacency using direction specification
    #        if direction == 'up':
    #            neighboring_nodes = node._upstream_nodes
    #        elif direction == 'down':
    #            neighboring_nodes = node._downstream_nodes
    #        elif direction == 'both':
    #            neighboring_nodes = (
    #                node._upstream_nodes + node._downstream_nodes)

    #        # search all neightbors to this node for unvisited nodes
    #        for n in node.neigbors:
    #            # if you find unvisited node, add it to nodes needing visit
    #            if n not in visited_nodes:
    #                stack.append(n)

    #    # should have hit all nodes in the graph at this point
    #    return visited_nodes


