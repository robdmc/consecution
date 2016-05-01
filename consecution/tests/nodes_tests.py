from unittest import TestCase
from consecution.nodes import Node

class SimpleTest(TestCase):
    def test_producer(self):
        a = Node('a')
        b = Node('b')
        c = Node('c')

