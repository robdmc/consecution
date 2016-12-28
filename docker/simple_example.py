#! /usr/bin/env python

# TODO: make the consecution install in the docker file read from pip
from __future__ import print_function

from consecution import Node, Pipeline


class N(Node):
    def process(self, item):
        print(item, self.name)
        self.push(item)


p = Pipeline(
    N('a') | [N('b'), N('c')] | N('d')
)
p.plot()

p.consume(range(5))
