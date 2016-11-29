.. _ref-consecution:

Code documentation
==================

Node
----------------
Here is stuff about nodes.

Example:

.. code-block:: python

    from consecution import Node

    class MyNode(Node):
        pass

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
