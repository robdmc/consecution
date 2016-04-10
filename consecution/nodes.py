class Node(object):
    def __init__(self, name):
        self.name = name
        self._upstream_nodes = []
        self._downstream_nodes = []

    def __str__(self):
        return 'N({})'.format(self.name)

    def __repr__(self):
        return self.__string__()

    @property
    def top_node(self):
        if self._upstream_nodes:
            return self._upstream_nodes[0].top_node
        else:
            return self

    @property
    def _self_and_downstreams(self):
        out = set(self)
        for node in self._downstream_nodes:
            out.add(node)
            # add further downstreams here

    @property
    def all_nodes(self):
        top_node = self.top_node
        for 





