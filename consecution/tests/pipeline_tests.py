import os
import sys

from collections import namedtuple, Counter
import shutil
import tempfile
from unittest import TestCase
from consecution.nodes import Node
from consecution.pipeline import Pipeline

Item = namedtuple('Item', 'value parent source')
class Item(object):
    def __init__(self, value, parent, source):
        self.value = value
        self.parent = parent
        self.source = source

    def build_source_list(self, source_list=None):
        source_list = [] if source_list is None else source_list
        source_list.append(self.source)
        if self.parent:
            self.parent.build_source_list(source_list)
        return source_list

    def get_path_string(self):
        return '|'.join([str(self.value)] + self.build_source_list()[::-1])

    def __str__(self):
        return self.get_path_string()

    def __repr__(self):
        return self.get_path_string()


class GlobalState(object):
    def __init__(self):
        self.final_items = []

class TestNode(Node):
    def process(self, item):
        self.push(
            Item(value=item.value, parent=item, source=self.name)
        )

class TestNode2(Node):
    def process(self, item):
        self.push(
            Item(value=('replace', item.value), parent=item, source=self.name)
        )


class ResultNode(Node):
    def process(self, item):
        self.global_state.final_items.append(item)

def item_generator():
    for ind in range(1, 3):
        yield Item(
            value=ind,
            parent=None,
            source='generator'
        )

class TestBase(TestCase):
    def setUp(self):
        a = TestNode('a')
        b = TestNode('b')
        c = TestNode('c')
        d = TestNode('d')
        even = TestNode('even')
        odd = TestNode('odd')
        g = TestNode('g')

        def even_odd(item):
            return ['even', 'odd'][item.value % 2]

        a | b | [c, d] | [even, odd, even_odd] | g

        self.pipeline = Pipeline(a, global_state=GlobalState())


class Printer(object):
    def __init__(self):
        self.txt = ""

    def write(self, txt):
        self.txt += txt

    def lines(self):
        for line in self.txt.split('\n'):
            yield line.strip()


class LoggingTests(TestBase):
    def test_logging(self):
        self.pipeline['g'].log('input')

        printer = Printer()
        sys.stdout = printer

        self.pipeline.consume(item_generator())
        sys.stdout = sys.__stdout__

        counter = Counter()
        for line in printer.lines():
            even_odd = line.split('|')[-1]
            counter.update({even_odd: 1})
        self.assertEqual(counter['even'], 2)
        self.assertEqual(counter['odd'], 2)


class ReplacementTests(TestBase):
    def test_replace_first(self):
        class Replacement(Node):
            def process(self, item):
                self.push(
                    Item(value=10 * item.value, parent=item, source=self.name)
                )

        self.pipeline['a'] = Replacement('a')
        self.pipeline['a'].log('output')

        printer = Printer()
        sys.stdout = printer
        self.pipeline.consume(item_generator())
        sys.stdout = sys.__stdout__
        self.assertEqual(printer.txt.count('10'), 1)
        self.assertEqual(printer.txt.count('20'), 1)

    def test_replace_even(self):
        class Replacement(Node):
            def process(self, item):
                self.push(
                    Item(value=10 * item.value, parent=item, source=self.name)
                )

        self.pipeline['even'] = Replacement('even')
        self.pipeline['g'].log('output')

        printer = Printer()
        sys.stdout = printer
        self.pipeline.consume(item_generator())
        sys.stdout = sys.__stdout__
        self.assertEqual(printer.txt.count('1'), 2)
        self.assertEqual(printer.txt.count('20'), 2)

        #IVE GOT REPLACEMENT CODE WRITTEN, BUT IM ONLY HALF WAY DONE TESTING IT.
        #RIGHT NOW I HAVE THE FIRST NODE TESTED.  WHAT I NEED TO DO NEXT IS TEST
        #MAYBE JUST THE EVEN SIDE OR THE ODD SIDE AND MAKE SURE REPLACEMENT
        #IS WORKING PROPERLY FOR NON FIRST NODES.

        #I ALSO WANT TO MAKE ROUTER BE ABLE TO ROUTE TO MULTIPLE DOWNSTREAM NODES
        #I ALSO WANT TO BE ABLE TO ADD BEGIN() AND END() METHODS TO THE PIPELINE
        #CLASS FOR SETTING UP AND TEARING DOWN GLOBAL STATE PROGRAMATICALLY

        #vvvvv I think this is now done
        #MAYBE THE .END() METHOD ON THE PIPELINE CLASS CAN SUPPORTS A
        #RETURN VALUE.  THIS VALUE WILL GET RETURNED WHEN DONE CONSUMING
        #AN ITERABLE AS WELL
        #^^^^^^^^^^^^^^^^

        # I THINK I MIGHT ALSO WANT A .RESET() METHOD DEFINED ON EACH NODE THAT
        # DEFAULTS TO NOHTHING, BUT THAT CAN BE OVERRIDEN BY USERS SO THAT
        # BY CALLING .RESET() ON A PIPELINE, IT AND ALL ITS NODES CAN BE RESET


class ConsumingTests(TestBase):
    def test_even_odd(self):
        self.pipeline['g'].add_downstream(
            ResultNode('result_node')
        )

        self.pipeline.consume(item_generator())

        expected_path_set = set([
            '1|generator|a|b|c|odd|g',
            '1|generator|a|b|d|odd|g',
            '2|generator|a|b|c|even|g',
            '2|generator|a|b|d|even|g',
        ])
        path_set = set(
            item.get_path_string() for item in
            self.pipeline.global_state.final_items
        )
        self.assertEqual(expected_path_set, path_set)


class ConstructingTests(TestBase):
    def test_printing(self):
        lines = repr(self.pipeline).split('\n')
        self.assertEqual(len(lines), 13)

    def test_plotting(self):
        # don't want to force a mock dependency, so make a simple mock here
        args_kwargs = []
        def return_calls(*args, **kwargs):
            args_kwargs.append(args)
            args_kwargs.append(kwargs)

        # assign my mock to the top node plot function
        self.pipeline.top_node.plot = return_calls

        # call pipeline plot
        self.pipeline.plot()

        # make sure top node plot was properly called
        self.assertEqual(args_kwargs[0], ('pipeline', 'png', False))
        self.assertEqual(args_kwargs[1], {})


