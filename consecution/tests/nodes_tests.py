import os
import shutil
import tempfile
from unittest import TestCase
from consecution.nodes import Node

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


        #a | [b, c | d]
        #a | [b, c | d]

        # THIS IS A PROBLEM.  I'M THINKING I WANT TO MAKE IT SO THAT
        # WHEN THIS IS ENCOUNTERED, [C, D] WILL GET FLATTENED INTO
        # THEIR CONTAINING LIST
        #print
        #print '*'*80
        #print [a, b] | c
        a |[b, [c, d] | e]
        #print '*'*80
        #a | [b, [d, e] | e]

        # wire up nodes using dsl
        #a | [
        #   b,
        #   c | [
        #           d,
        #           #e  | [f, g, h, i, my_router] | j
        #           e  | [f, g, h, i] | j
        #   ] | k
        #] | l | [m, n]

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
        dup = Node('c')
        with self.assertRaises(ValueError):
            self.top_node.add_downstream(dup)

    def test_multi_root(self):
        self.do_wiring()
        other_root = Node('dual_root')
        other_root.add_downstream(self.top_node._downstream_nodes[0])

        print
        print '*'*80
        print 'initial_node_set'
        print self.top_node.initial_node_set

        with self.assertRaises(ValueError):
            other_root.top_node

    def test_non_node_connect(self):
        node = Node('a')
        other = 'not a node'
        with self.assertRaises(ValueError):
            node.add_downstream(other)

    def test_write(self):
        self.do_wiring()
        out_file = os.path.join(self.temp_dir, 'out.png')
        self.top_node.draw_graph(out_file)
        #uncomment the next line if you want to look at the graph
        os.system('cp {} /tmp'.format(out_file))


class DSLWiringTests(ExplicitWiringTests):
    def do_wiring(self):
        self.do_graph_wiring()


#  THIS IS A COMPLICATED TEST TOPOLOGY I MIGHT WANT TO USE
# pre = Pass('pre')
# a = Pass('a')
# b = Pass('b')
# c = Pass('c')
# d = Pass('d')
# e = Pass('e')
# f = Pass('f')
# g = Pass('g')
# h = Pass('h')
# i = Pass('i')
# j = Pass('j')
# k = Pass('k')
# m = Printer('m')
# producer | a | [
#     b,
#     c | [
#             d,
#             e  | [f, g, h, k, my_router] | i
#     ] | j
# ] | m
