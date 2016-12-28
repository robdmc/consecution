from __future__ import print_function
from collections import namedtuple, Counter
from unittest import TestCase
from consecution.nodes import Node, GroupByNode
from consecution.pipeline import Pipeline, GlobalState
from consecution.tests.testing_helpers import print_catcher

Item = namedtuple('Item', 'value parent source')


class Item(object):  # pragma: no cover (just a testing helper)
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


class TestNode(Node):
    def process(self, item):
        self.push(
            Item(value=item.value, parent=item, source=self.name)
        )


class ResultNode(Node):
    def process(self, item):
        self.global_state.final_items.append(item)


class BadNode(Node):
    def begin(self):
        self.push(1)

    def process(self, item):  # pragma: no cover  this should never get hit.
        self.push(item)


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

        self.pipeline = Pipeline(a, global_state=GlobalState(final_items=[]))


class GlobalStateUnitTests(TestCase):
    def test_kwargs_passed(self):
        g = GlobalState(custom_name='custom')
        p = Pipeline(TestNode('a'), global_state=g)
        self.assertTrue(p.global_state.custom_name == 'custom')
        self.assertTrue(p.global_state['custom_name'] == 'custom')

    def test_printing(self):
        g = GlobalState(custom_name='custom')
        with print_catcher() as catcher1:
            print(g)

        with print_catcher() as catcher2:
            print(repr(g))

        self.assertTrue(
            'GlobalState(\'custom_name\')' in catcher1.txt)
        self.assertTrue(
            'GlobalState(\'custom_name\')' in catcher2.txt)


class OrOpTests(TestCase):
    def test_ror(self):
        a = Node('a')
        b = Node('b')
        c = Node('c')
        d = Node('d')

        p = Pipeline(a | ([b, c] | d))
        with print_catcher() as catcher:
            print(p)
        self.assertTrue('a | [b, c]' in catcher.txt)
        self.assertTrue('c | d' in catcher.txt)
        self.assertTrue('b | d' in catcher.txt)


class ManualFeedTests(TestCase):
    def test_manual_feed(self):

        class N(Node):
            def begin(self):
                self.global_state.out_list = []

            def process(self, item):
                self.global_state.out_list.append(item)

        pipeline = Pipeline(TestNode('a') | N('b'))
        pushed_list = []
        for item in item_generator():
            pushed_list.append(item)
            pipeline.push(item)
        pipeline.end()
        self.assertEqual(len(pipeline.global_state.out_list), 2)


class PipelineUnitTests(TestCase):
    def test_push_in_begin(self):
        pipeline = Pipeline(BadNode('a') | TestNode('b'))
        with self.assertRaises(AttributeError):
            with print_catcher('stderr'):
                pipeline.begin()

    def test_no_process(self):
        class N(Node):
            pass

        pipe = Pipeline(N('a') | N('b'))
        with self.assertRaises(NotImplementedError):
            pipe.consume(range(3))

    def test_bad_route(self):
        def bad_router(item):
            return 'bad'

        class N(Node):
            def process(self, item):
                self.push(item)

        pipeline = Pipeline(N('a') | [N('b'), N('c'), bad_router])

        with self.assertRaises(ValueError):
            pipeline.consume(range(3))

    def test_bad_node_lookup(self):
        pipeline = Pipeline(TestNode('a') | TestNode('b'))

        with self.assertRaises(KeyError):
            pipeline['c']

    def test_bad_replacement_name(self):
        pipeline = Pipeline(TestNode('a') | TestNode('b'))
        with self.assertRaises(ValueError):
            pipeline['b'] = TestNode('c')

    def test_flattened_list(self):
        pipeline = Pipeline(
            TestNode('a') | [[Node('b'), Node('c')]])

        with print_catcher() as catcher:
            print(pipeline)

        self.assertTrue('a | [b, c]' in catcher.txt)

    def test_logging(self):
        pipeline = Pipeline(TestNode('a') | TestNode('b'))
        pipeline['a'].log('output')
        pipeline['b'].log('input')
        with print_catcher() as catcher:
            pipeline.consume(item_generator())
        text = """
            node_log,what,node_name,item
            node_log,output,a,1|generator|a
            node_log,input,b,1|generator|a
            node_log,output,a,2|generator|a
            node_log,input,b,2|generator|a
        """
        for line in text.split('\n'):
            self.assertTrue(line.strip() in catcher.txt)

    def test_reset(self):
        class N(Node):
            def begin(self):
                self.was_reset = False

            def process(self, item):
                self.push(item)

            def reset(self):
                self.was_reset = True

        pipe = Pipeline(N('a') | N('b'))
        pipe.consume(range(3))
        self.assertFalse(pipe['a'].was_reset)
        self.assertFalse(pipe['b'].was_reset)

        pipe.reset()

        self.assertTrue(pipe['a'].was_reset)
        self.assertTrue(pipe['b'].was_reset)


class LoggingTests(TestBase):
    def test_logging(self):
        self.pipeline['g'].log('input')

        with print_catcher() as printer:
            self.pipeline.consume(item_generator())

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

        with print_catcher() as printer:
            self.pipeline.consume(item_generator())
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

        with print_catcher() as printer:
            self.pipeline.consume(item_generator())
        self.assertEqual(printer.txt.count('1'), 2)
        self.assertEqual(printer.txt.count('20'), 2)

    def test_replace_no_router(self):
        a = TestNode('a')
        b = TestNode('b')
        pipe = Pipeline(a | b)
        pipe['b'] = TestNode('b')
        with print_catcher() as catcher:
            print(pipe)
        self.assertTrue('a | b' in catcher.txt)


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
        self.assertEqual(args_kwargs[0], ('pipeline', 'png'))
        self.assertEqual(args_kwargs[1], {})


class Batch(GroupByNode):
    def begin(self):
        self.global_state.batches = []

    def key(self, item):
        return item // 3

    def process(self, batch):
        self.global_state.batches.append(batch)


class GroupByTests(TestCase):
    def test_batching(self):
        pipe = Pipeline(Batch('a'))
        pipe.consume(range(9))
        self.assertEqual(
            pipe.global_state.batches,
            [[0, 1, 2], [3, 4, 5], [6, 7, 8]]
        )

    def test_undefined_key(self):
        class B(GroupByNode):
            def process(self, item):  # pragma: no cover
                pass

        pipe = Pipeline(B('a'))

        with self.assertRaises(NotImplementedError):
            pipe.consume(range(9))

    def test_undefined_process(self):
        class B(GroupByNode):
            def key(self, item):
                pass

        pipe = Pipeline(B('a'))

        with self.assertRaises(NotImplementedError):
            pipe.consume(range(9))
