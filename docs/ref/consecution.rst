.. _ref-consecution:

Code documentation
==================

Node
----
Nodes are the fundamental processing unit in consecution.  A node is created by
inheriting from the `consecution.Node` class.  You are free to declare as many
attributes and methods on a node class as you wish.  You should not override the
constructor unless you really know what you're doing.  Instead, any
initialization you wish to perform can be carried out in the `.begin()` method.
In the descriptions below, it is assumed that the nodes being discussed have
been wired together into a pipeline and are ready to consume items.

See the 
`Github README
<https://github.com/robdmc/consecution/blob/master/README.md>`_
for examples  of how to wire nodes into pipelines.

Reserved Method Names
~~~~~~~~~~~~~~~~~~~~~
The following Node methods are not intended to be overridden, so you should not
define methods with these names in your node implementations unless you really
know what you are doing.

*  `top_node`
*  `initial_node_set`
*  `terminal_node_set`
*  `root_nodes`
*  `all_nodes`
*  `log`
*  `top_down_make_repr`
*  `top_down_call`
*  `depth_first_search`
*  `breadth_first_search`
*  `search`
*  `add_downstream`
*  `remove_downstream`
*  `plot`

There are also a number of private method names you should avoid.  These can be
identified by looking at the `source code 
<https://github.com/robdmc/consecution/blob/master/consecution/nodes.py>`_


Examples
~~~~~~~~

Here is the simplest possible node you could construct:

.. code-block:: python

    from consecution import Node

    class MyNode(Node):
        def process(self, item):
            self.push(item)

All nodes acquire a `.push()` method when they are wired into a pipeline.  You
can call this method anywhere in your class except in the `.begin()` method.
The `.push(item)` method will take its argument and send it to the `.process()`
methods of the nodes that are immediately downstream in your pipeline graph.

Here is an example node defining all methods you can override.  The
functionality of each method is explained in the code comments.

.. code-block:: python

    from consecution import Node

    class MyNode(Node):
        def begin(self):
            # This sets up whatever state you want to exist before the
            # node begins processing any data.  You can think of it as an
            # init method that runs just before the node starts processing.
            # In this example, we initialize a simple counter
            self.counter = 0

        def process(self, item):
            # This is the method that defines the processing you want to perform
            # on every item the node processes.  You can place whatever logic
            # you want here, including calls the the .push() method.
            # In this example, we update the counter and push the item
            # downstream.
            self.counter += 1
            self.push(item)

        def end(self):
            # This method is called right after all items are processed.
            # This happens  when the iterator being consumed by the pipeline
            # is exhausted.  At that point the .end() methods of all nodes
            # in the pipeline are called.  This is a good place for you to
            # push any summary information downstream.
            # In this example we push the results of our counter
            self.push(self.counter)

        def reset(self):
            # A pipeline can be reused and reset back to its initial condition.
            # It does this by calling the .reset() method of all its member
            # nodes.  You can place whatever code you want here to reset your
            # node to its initial state.
            # In this example, we simply reset the counter.
            self.counter = 0

Node API Documentation
~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: consecution.nodes.Node
    :members:

GroupBy Node
~~~~~~~~~~~~~~~~~~~~~~
.. autoclass:: consecution.nodes.GroupByNode
    :members:



Pipeline
-----------------
In consecution, nodes are wired into pipelines that consume python iterables.
There are two levels of abstraction for wiring nodes together.  These
abstractions are defined at the Node level.  Once the wiring is complete, you
can pass any of the constituent nodes to the Pipeline constructor, which is
responsible for examining your connections and coordinating the nodes into a
coherent set of operations.


Manually Connecting Nodes
-------------------------
The Node base class is equipped with an ``.add_downstream(other_node)`` method.
This method provides detailed control over how nodes are wired together. It
simply adds ``other_node`` as a downstream relation.

Here is an example of creating a pipeline with one top node that broadcasts
items to two downstream nodes, and then collects their results into a single
output node.

.. code-block:: python

    from consecution import Pipeline, Node
    from __future__ import print_function

    class SimpleNode(Node):
        def process(self, item):
            print('{} processing {}'.format(self.name, item))
            self.push(item)

    top = SimpleNode('top')
    left = SimpleNode('left')
    right = SimpleNode('right')
    output = SimpleNode('output')

    top.add_downstream(left)
    top.add_downstream(right)

    left.add_downstream(output)
    right.add_downstream(output)

    pipe = Pipeline(top)

    pipe.consume(range(2))


Node Connection Mini-language
-----------------------------
Consecution provides a concise domain-specific-language (DSL) for creating
directed acyclic graphs.  This is the preferred method for connecting nodes into
a pipeline.  However, you may occasionally find that your desired topology is not
easy to express in the DSL.  For these situations, consecution provides a
lower-level escape hatch that allowes you to manually connect two nodes
together.  These two levels of abstraction provide a very powerful interface for
constructing complex pipelines.

The DSL is inspired by the unix syntax for chaining together the inputs and
outputs of different programs at the bash prompt.  You use the pipe symbol ``|``
to connect nodes together.  These pipe operators will always return an object of
one of the nodes in your connected topology. Below is an example of creating a
simple linear pipeline.

.. code-block:: python

    from consecution import Pipeline, Node
    from __future__ import print_function

    class SimpleNode(Node):
        def process(self, item):
            print('{} processing {}'.format(self.name, item))
            self.push(item)

    left = SimpleNode('left')
    middle = SimpleNode('middle')
    right = SimpleNode('right')

    # wire nodes together with bash-like pipe operator
    node_object = left | middle | right

    # You can now pass the node object into a pipeline constructor
    pipe = Pipeline(node_object)
    pipe.consume(range(2))

In order to create a directed acyclic graph (DAG) you need four basic
constructs:

* Send data from one node to a single other node
* Broadcast data from one node to a set of other nodes
* Route data from one node to one of a set of other nodes
* Gather output from several nodes into one node.

The DSL provides mechanisms for each of these constructs, and we will look at
each in turn.

Send data from single node to single node
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Use simple bash-like pipe syntax to send data from a single node to another
node.

.. code-block:: python

    # Send data from one to to a single other node using bash-like piping.
    node1 | node2



Broadcast data from single node to multiple node
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Broadcasting is accomplished by piping to a list of nodes.  In the following
example, ``node1`` will send each item it pushes to ``node2``, ``node3``, and
``node4``.

.. code-block:: python

    # Broadcast to a set of nodes by piping to a list
    node1 | [node2, node3, node4]

Routing from one node to one of multiple nodes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Routing is accomplished by piping to a list that contains a single callable and
any number of nodes.  The following example will send even numbers to
``even_node`` and odd numbers to ``odd_node``.

.. code-block:: python

    # Define a node class
    class N(Node):
        def process(self, item):
            self.push(item)

    # Define a routing function.  It takes a single argument being the item
    # you pushed.  It should return a string with the name of the node
    # to which that item should be routed.
    def route_func(item):
        if item % 2 == 0:
            return 'even_node'
        else:
            return 'odd_node'

    # Pipe to a list of nodes and a callable to achieve routing
    N('top_node') | [N('even_node'), N('odd_node'), route_func]


Gather output from multiple nodes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Gathering output from a set of nodes is as simple as piping a list of nodes (and
possibly a route function) to a single node.  In this example, the outputs of
``node2``, ``node3``, and ``node4`` will all be sent to ``node5``.

.. code-block:: python

    # Broadcast to a set of nodes by piping to a list
    node1 | [node2, node3, node4] | node5


.. autoclass:: consecution.pipeline.Pipeline
    :members:
