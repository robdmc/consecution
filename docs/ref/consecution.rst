.. _ref-consecution:

Code documentation
==================

Node
----
Nodes are the fundamental processing unit in consecution.  A node is created by
subclassing from the `consecution.Node` class.  You are free to declare as many
attributes and methods on a node class as you see fit.  It is not recommended
practice to override the constructor.  Any initialization you wish to perform on
the node state can be accomplished by defining a `.begin()` method.  In the
descriptions below, it is assumed that the nodes being discussed have been wired
together into a pipeline, and are ready to comsume items.

Reserved Method Names
~~~~~~~~~~~~~~~~~~~~~
The following Node methods are not intended to be overridden, so you should not
define methods with these names in your node implementations unless you really
know what you are doing.

*  top_node
*  initial_node_set
*  terminal_node_set
*  root_nodes
*  all_nodes
*  log
*  top_down_make_repr
*  top_down_call
*  depth_first_search
*  breadth_first_search
*  search
*  add_downstream
*  remove_downstream
*  plot

There are also a number of private method names you should avoid.  These can be
identified by looking at the `source code 
<https://github.com/robdmc/consecution/blob/master/consecution/nodes.py>`_


Here is the simplest possible node you could construct:

.. code-block:: python

    from consecution import Node

    class MyNode(Node):
        def process(self, item):
            self.push(item)

All notes acquire a `.push()` method when they are wired into a pipeline.  You
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


.. autoclass:: consecution.nodes.Node
    :members:

Pipeline
-----------------
Here is stuff about pipelines.

Example:

.. code-block:: python

    from consecution import Pipeline, Node

    class MyNode(Node):
        pass

    p = Pipeline(MyNode('a') | MyNode('b'))

.. autoclass:: consecution.pipeline.Pipeline
    :members:
