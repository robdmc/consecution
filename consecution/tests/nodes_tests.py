import os
from collections import namedtuple
import shutil
import tempfile
from unittest import TestCase
import subprocess

from mock import patch

from consecution.nodes import Node
from consecution.tests.testing_helpers import print_catcher

def dot_installed():
    p = subprocess.Popen(
        ['bash', '-c', 'which dot'], stdout=subprocess.PIPE)
    p.wait()
    result = p.stdout.read().decode("utf-8")
    return 'dot' in result


class FakeDigraph(object):  # pragma: no cover
    def __init__(self, *args, **kwargs):
        pass
    def node(self, *args, **kwargs):
        pass
    def edge(self, *args, **kwargs):
        pass
    def render(self, *args, **kwargs):
        raise RuntimeError('fake runtime error')


class NodeUnitTests(TestCase):
    def test_bad_logging_args(self):
        n = Node('a')
        with self.assertRaises(ValueError):
            n.log('bad')

    def test_bad_top_down_make_repr_call(self):
        n = Node('a')
        with self.assertRaises(ValueError):
            n.top_down_make_repr()

    def test_args_as_atts(self):
        n = Node('my_node', silly_attribute='silly')
        self.assertEqual(n.silly_attribute, 'silly')

    def test_comparisons(self):
        a = Node('a')
        b = Node('b')

        self.assertTrue(a == a)
        self.assertFalse(a == b)

        self.assertTrue(a < b)
        self.assertFalse(b < a)

    def test_bad_flattening(self):
        a = Node('a')
        with self.assertRaises(ValueError):
            a | 7

    #def test_remove_non_existent_node(self):
    #    a = Node('a')
    #    b = Node('b')
    #    c = Node('c')
    #    a.add_downstream(b)
    #    a.remove_downstream(c)



    @patch(
        'consecution.nodes.Node._build_pydot_graph', lambda a: FakeDigraph())
    def test_graphviz_not_installed(self):
        a = Node('a')
        b = Node('b')
        p = a | b
        with self.assertRaises(RuntimeError):
            with print_catcher('stderr') as printer:
                p.plot()
        self.assertTrue('graphviz' in printer.txt)

    def test_no_getitem(self):
        a = Node('a')
        with self.assertRaises(ValueError):
            a['b']

    def test_bad_slot_name(self):
        a = Node('a')
        b = Node('b')
        with self.assertRaises(ValueError):
            a._get_exposed_slots(b, 'bad_arg')


class ExplicitWiringTests(TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def do_wiring(self):
        self.do_explicit_wiring()

    def do_explicit_wiring(self):
        # define nodes
        a = Node('a')
        b = Node('b')
        c = Node('c')
        d = Node('d')
        e = Node('e')
        f = Node('f')
        g = Node('g')
        h = Node('h')
        i = Node('i')
        j = Node('j')
        k = Node('k')
        l = Node('l')
        m = Node('m')
        n = Node('n')

        # save a list of all nodes
        self.node_list = [a, b, c, d, e, f, g, h, i, j, k, l, m, n]
        self.top_node = a

        # wire up the nodes
        a.add_downstream(b)
        a.add_downstream(c)

        c.add_downstream(d)
        c.add_downstream(e)

        e.add_downstream(f)
        e.add_downstream(g)
        e.add_downstream(h)
        e.add_downstream(i)

        f.add_downstream(j)
        g.add_downstream(j)
        h.add_downstream(j)
        i.add_downstream(j)

        d.add_downstream(k)
        j.add_downstream(k)

        b.add_downstream(l)
        k.add_downstream(l)

        l.add_downstream(m)
        l.add_downstream(n)

        # same network in graph notation
        # a | [
        #    b,
        #    c | [
        #            d,
        #            e  | [f, g, h, i, my_router] | j
        #    ] | k
        # ] | l [m, n]

    def do_graph_wiring(self):
        # define nodes
        a = Node('a')
        b = Node('b')
        c = Node('c')
        d = Node('d')
        e = Node('e')
        f = Node('f')
        g = Node('g')
        h = Node('h')
        i = Node('i')
        j = Node('j')
        k = Node('k')
        l = Node('l')
        m = Node('m')
        n = Node('n')

        # save a list of all nodes
        self.node_list = [a, b, c, d, e, f, g, h, i, j, k, l, m, n]
        self.top_node = a

        # wire up nodes using dsl (if statement just to make flake8 work)
        if True:  # flake8: noqa
            a | [
                   b,
                   c | [
                           d,
                           e  | [f, g, h, i] | j
                       ] | k
                ] | l | [m, n]

    def test_connections(self):
        Conns = namedtuple('Conns', 'node upstreams downstreams')
        self.do_wiring()
        n = {
            node.name: Conns(
                node.name,
                {u.name for u in node._upstream_nodes},
                {d.name for d in node._downstream_nodes}
            )
            for node in self.node_list
        }
        self.assertEqual(n['a'].upstreams, set())
        self.assertEqual(n['a'].downstreams, {'b', 'c'})

        self.assertEqual(n['b'].upstreams, {'a'})
        self.assertEqual(n['b'].downstreams, {'l'})

        self.assertEqual(n['c'].upstreams, {'a'})
        self.assertEqual(n['c'].downstreams, {'d', 'e'})

        self.assertEqual(n['e'].upstreams, {'c'})
        self.assertEqual(n['e'].downstreams, {'f','g','h','i'})

        self.assertEqual(n['f'].upstreams, {'e'})
        self.assertEqual(n['f'].downstreams, {'j'})

        self.assertEqual(n['g'].upstreams, {'e'})
        self.assertEqual(n['g'].downstreams, {'j'})

        self.assertEqual(n['h'].upstreams, {'e'})
        self.assertEqual(n['h'].downstreams, {'j'})

        self.assertEqual(n['i'].upstreams, {'e'})
        self.assertEqual(n['i'].downstreams, {'j'})

        self.assertEqual(n['d'].upstreams, {'c'})
        self.assertEqual(n['d'].downstreams, {'k'})

        self.assertEqual(n['j'].upstreams, {'f','g','h','i'})
        self.assertEqual(n['j'].downstreams, {'k'})

        self.assertEqual(n['k'].upstreams, {'j', 'd'})
        self.assertEqual(n['k'].downstreams, {'l'})

        self.assertEqual(n['l'].upstreams, {'k', 'b'})
        self.assertEqual(n['l'].downstreams, {'m', 'n'})

    def test_all_nodes(self):
        self.do_wiring()
        expected_set = set(self.node_list)
        all_nodes_set = [
            set(node.all_nodes) for node in self.node_list
        ]
        self.assertTrue(all(
            [expected_set == found_set for found_set in all_nodes_set]))

    def test_top_node(self):
        self.do_wiring()
        top_node_set = {node.top_node for node in self.node_list}
        self.assertEqual(top_node_set, {self.top_node})

    def test_duplicate_node(self):
        self.do_wiring()

        # this test is funky in that it has assertion in a loop.
        # but I wanted to be sure cycles are detected everywhere 
        for name in [n.name for n in self.top_node.all_nodes]:
            dup = Node(name)
            with self.assertRaises(ValueError):
                self.top_node.add_downstream(dup)

    def test_acyclic(self):
        self.do_wiring()

        # this test is funky in that it has assertion in a loop.
        # but I wanted to be sure dups are detected everywhere 
        for node in self.top_node.all_nodes:
            with self.assertRaises(ValueError):
                node.add_downstream(self.top_node)

    def test_multi_root(self):
        self.do_wiring()
        other_root = Node('dual_root')
        other_root.add_downstream(self.top_node._downstream_nodes[0])

        with self.assertRaises(ValueError):
            other_root.top_node

    def test_non_node_connect(self):
        node = Node('a')
        other = 'not a node'
        with self.assertRaises(ValueError):
            node.add_downstream(other)

    def test_write(self):
        # don't run coverage on this because won't test travis with
        # both dot installed and not installed.
        if dot_installed(): # pragma: no cover 
            self.do_wiring()
            out_file = os.path.join(self.temp_dir, 'out.png')
            self.top_node.plot(out_file)
            #uncomment the next line if you want to look at the graph
            os.system('cp {} /tmp'.format(out_file))

    def test_write_bad_kind(self):
        self.do_wiring()
        with self.assertRaises(ValueError):
            self.top_node.plot(kind='bad')

    def test_bad_search_direction(self):
        self.do_wiring()
        with self.assertRaises(ValueError):
            self.top_node.breadth_first_walk(direction='bad')

    def test_bad_search_method(self):
        self.do_wiring()
        with self.assertRaises(ValueError):
            self.top_node.walk(how='bad')


class DSLWiringTests(ExplicitWiringTests):
    def do_wiring(self):
        self.do_graph_wiring()

class TopDownCallTests(TestCase):
    def test_call_order_okay(self):

        # a toy class that holds a class variable
        # tracking what order objects get called in
        class MyNode(Node):
            call_list = []
            def end(self):
                self.__class__.call_list.append(self)

        a = MyNode('a')
        b = MyNode('b')
        c = MyNode('c')
        d = MyNode('d')
        e = MyNode('e')
        f = MyNode('f')
        g = MyNode('g')

        a | [
            b | c,
            d | e | f
        ] |  g
        a.top_node.top_down_call('end')

        # make a dictionary with order in which nodes
        # were called
        call_number = {
            node: ind for (ind, node) in enumerate(a.__class__.call_list)}

        # make sure ording of one branch is right
        self.assertTrue(call_number[a] < call_number[b])
        self.assertTrue(call_number[b] < call_number[c])
        self.assertTrue(call_number[c] < call_number[g])

        # make sure ordering of other branch is okay
        self.assertTrue(call_number[a] < call_number[d])
        self.assertTrue(call_number[d] < call_number[e])
        self.assertTrue(call_number[e] < call_number[f])
        self.assertTrue(call_number[f] < call_number[g])


class BreadthFirstSearchTests(TestCase):
    def test_top_down_order(self):
        a = Node('a')
        b = Node('b')
        c = Node('c')
        d = Node('d')
        e = Node('e')
        f = Node('f')
        g = Node('g')
        h = Node('h')
        i = Node('i')

        def silly_router(item):  # pragma: no cover
            return 0

        a | [b, c] | [d, e, f, silly_router] | [h, i]
        nodes =  a.top_node.breadth_first_walk(
            direction='down', as_ordered_list=True)
        level5 = {nodes.pop() for nn in range(2)}
        level4 = {nodes.pop() for nn in range(3)}
        level3 = {nodes.pop() for nn in range(2)}
        level2 = {nodes.pop() for nn in range(2)}
        level1 = {nodes.pop() for nn in range(1)}

        self.assertEqual(level1, {a})
        self.assertEqual(level2, {b, c})
        self.assertEqual(len(level3), 2)
        self.assertEqual(level4, {d, e, f})
        self.assertEqual(level5, {h, i})

    def test_bottom_up_order(self):
        a = Node('a')
        b = Node('b')
        c = Node('c')
        d = Node('d')
        e = Node('e')
        f = Node('f')
        g = Node('g')
        h = Node('h')

        def silly_router(item):  # pragma: no cover
            return 0

        a | [b, c] | [d, e, f, silly_router] | h
        nodes =  h.breadth_first_walk(direction='up', as_ordered_list=True)
        nodes = nodes[::-1]
        level5 = {nodes.pop() for nn in range(1)}
        level4 = {nodes.pop() for nn in range(3)}
        level3 = {nodes.pop() for nn in range(2)}
        level2 = {nodes.pop() for nn in range(2)}
        level1 = {nodes.pop() for nn in range(1)}

        self.assertEqual(level1, {a})
        self.assertEqual(level2, {b, c})
        self.assertEqual(len(level3), 2)
        self.assertEqual(level4, {d, e, f})
        self.assertEqual(level5, {h})

class PrintingTests(TestCase):
    def setUp(self):
        # define nodes
        a = Node('a')
        b = Node('b')
        c = Node('c')
        d = Node('d')
        e = Node('e')
        f = Node('f')
        g = Node('g')
        h = Node('h')
        i = Node('i')
        j = Node('j')
        k = Node('k')
        l = Node('l')
        m = Node('m')
        n = Node('n')

        class DummyPipeline(object):
            pass

        pipeline = DummyPipeline()

        # save a list of all nodes
        self.node_list = [a, b, c, d, e, f, g, h, i, j, k, l, m, n]
        self.top_node = a

        def my_router(item):  # pragma: no cover
            return 'm'

        # wire up nodes using dsl
        a | [
               b,
               c | [
                       d,
                       e  | [f, g, h, i] | j
                   ] | k
            ] | l | [m, n, my_router]

        for node in self.top_node.all_nodes:
            node.pipeline = pipeline

    def test_nothing(self):
        self.top_node.top_down_make_repr()
        lines = sorted([
            line.strip()
            for line in self.top_node.pipeline._node_repr.split('\n')
            if line.strip()
        ])
        expected_lines = sorted([
            'a | [b, c]',
            'b | l',
            'c | [d, e]',
            'd | k',
            'e | [f, g, h, i]',
            'f | j',
            'g | j',
            'h | j',
            'i | j',
            'j | k',
            'k | l',
            'l | l.my_router',
            'l.my_router | [m, n]',
        ])
        self.assertEqual(lines, expected_lines)


class RoutingTests(TestCase):
    def test_nothing(self):
        a = Node('a')
        b = Node('b')
        c = Node('c')
        d = Node('d')
        e = Node('e')
        f = Node('f')
        g = Node('g')
        h = Node('h')
        i = Node('i')
        j = Node('j')
        k = Node('k')
        m = Node('m')
        bb = Node('bb')
        ee = Node('ee')

        def silly_router(item):  # pragma: no cover
            return 0

        class ClassRouter(object):  # pragma: no cover
            def __call__(self, arg):
                return arg

        a | [b, c, ClassRouter()] |[d, e, silly_router]
