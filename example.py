#! /usr/bin/env python

from __future__ import print_function
from consecution import Node, Pipeline


# Define your node by inheriting from consecution.Node
class N(Node):
    def process(self, item):
        # simply print the item and push it on to downstream nodes
        print('{:>15} processing {}'.format(self.name, item))
        self.push(item)

# define a pipeline by wiring nodes together with bash-like pipe syntax
pipe = Pipeline(
    N('one') | N('two') | N('three')
)

# print a representation of the pipeline to the console
print(pipe)

# run the pipeline by feeding it a small list of letters
print('=' * 30 + ' consuming ' + '=' * 30)
pipe.consume(['A', 'B', 'C'])
