import traceback
import asyncio
import pickle
import sys
import time
import inspect
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from functools import partial



#############################################################
def my_blocking_code1(name, item):
    time.sleep(1)
    #print('{} executing block1 on {}'.format(name, item))
    #return 'ret_from_block1'

def my_blocking_code2(name, item):
    #print('{} executing block2 on {}'.format(name, item))
    time.sleep(1)
    return ('result2', name, item)

#############################################################

def get_obj_path(obj):
    try:
        module_name = obj.__module__
    except AttributeError:
        module_name = ''
    if inspect.isfunction(obj):
        object_name = obj.__name__
    else:
        object_name = obj.__class__.__name__
    return module_name, object_name



def error_wrapper(f, log_errors, *args, **kwargs):
        try:
            return (True, f(*args, **kwargs))
        except:
            if log_errors:
                log_errors(sys.exc_info())
            return (False, sys.exc_info())

async def make_job(function, node_obj, *args, **kwargs):
    """
    returns succeeded, result
    """
    try:
        #TODO: only need to run this check if doing process pool
        pickle.dumps(function)
    except AttributeError:
        msg = (
            '\n\nProblem pickling the function:\n\n'
            '{1}() defined in module {0}\n'
            '\nThis can happen if you are using processes instead of threads\n'
            'and your function is not defined\n'
            'in the module scope.  In other words, you can\'t\n'
            'use functions that are defined in other functions.\n'
        ).format(*get_obj_path(function))
        raise ValueError(msg)

    func_to_exec = partial(
        error_wrapper, function, node_obj._log_errors, *args, **kwargs)
    return node_obj._loop.run_in_executor(node_obj.executor, func_to_exec)

#############################################################

def log_errors(exc_info_tup, node=None):
    print('v' * 78, file=sys.stderr)
    traceback.print_tb(exc_info_tup[2], file=sys.stderr)
    print(file=sys.stderr)
    print(exc_info_tup[0], file=sys.stderr)
    print(exc_info_tup[1], file=sys.stderr)
    if node is not None:
        print('Error occured in node: {}'.format(node))
    print('^' * 78, file=sys.stderr)


class BaseNode:
    executor = ProcessPoolExecutor(max_workers=10)
    #executor = ThreadPoolExecutor(max_workers=10)

    def __init__(
            self, name='', log_errors=True, loop=None, upstream=None,
            downstream=None):

        self._downstream_nodes = []
        self._upstream_nodes = []
        self._queue = asyncio.Queue(2)
        self._loop = loop if loop else asyncio.get_event_loop()
        self._log_errors = log_errors
        self.name = name
        self._routing_function = None
        self.consecutor = None
        self.edge_kwargs_list = []
        self.node_kwargs = dict(name=self.name, shape='rectangle')


        if upstream:
            self.add_upstream_node(upstream)
        if downstream:
            self.add_downstream_node(downstream)

    def __str__(self):
        return '<{}>'.format(self.name)
    def __repr__(self):
        return self.__str__()


    def validate_outputs(self, downstreams):
        if len(downstreams) == 0:
            msg = (
                'Error connecting {} to {}.\n'
                'There must be at least one node to connect to.'
            ).format(self, downstreams)
            raise ValueError(msg)

        if len(self.terminal_node_set) > 1 and len(downstreams) > 1:
            msg = (
                'Error connecting {} to {}.\n'
                'Many-to-many connections are not permitted'
            ).format(self, downstreams)
            raise ValueError(msg)
        self._detect_cycles(self.upstream_set, downstreams)

    def connect_outputs(self, *downstreams):
        downstreams = list(downstreams)
        self.validate_outputs(downstreams)
        for node in self.terminal_node_set:
            self.add_downstream_node(*downstreams)

    def _validate_or_operator_args(self, other):
        # define a default error message
        default_msg = (
            '\n\nError connecting {} to {}.\n'
            'Only nodes or list of nodes or callables are allowed.'
        ).format(self, other)

        # basenodes are okay
        if isinstance(other, BaseNode):
            return

        # make sure input lists are valid
        if isinstance(other, list):
            # count the number of elements of each type
            num_base_nodes, num_callables, num_bad_kinds = 0, 0, 0
            for el in other:
                if isinstance(el, BaseNode):
                    num_base_nodes += 1
                elif hasattr(el, '__call__'):
                    num_callables += 1
                else:
                    num_bad_kinds += 1

            if num_bad_kinds > 0:
                raise ValueError(default_msg)

            if num_callables > 1:
                msg = (
                    '\n\nError connecting {} to {}.\n'
                    'Mutliple routing functions found.'
                ).format(self, other)

        # everything but a node or a list is an error
        else:
            raise ValueError(default_msg)


    def __or__(self, other):

        # make sure arguments are valid
        self._validate_or_operator_args(other)

        # convert all input to list form
        if isinstance(other, BaseNode):
            other = [other]

        # separate node elements from routing function elements
        downstream_nodes = [
            el for el in other if isinstance(el, BaseNode)]
        routers = [
            el for el in other if hasattr(el, '__call__')]

        # if only one downstream node, then just connect it
        if len(downstream_nodes) == 1:
            self.connect_outputs(*downstream_nodes)
        # otherwise wire up a branching node
        else:
            branching_node = BranchingNode(name=self.name)
            if routers:
                branching_node.set_routing_function(routers[0])
            self.connect_outputs(branching_node)
            branching_node.connect_outputs(*downstream_nodes)

        out = list(self.terminal_node_set)
        return out[0] if len(out) == 1 else out

    def validate_inputs(self, upstreams):
        if len(upstreams) == 0:
            msg = (
                'Error connecting {} to {}.\n'
                'There must be at least one node to connect to.'
            ).format(upstreams, self)
            raise ValueError(msg)

        if len(self.initial_node_set) > 1 and len(upstreams) > 1:
            msg = (
                'Error connecting {} to {}.\n'
                'Many-to-many connections are not permitted'
            ).format(upstreams, self)
            raise ValueError(msg)
        self._detect_cycles(upstreams, self.downstream_set)

    def connect_inputs(self, *upstreams):
        self.validate_inputs(upstreams)
        for input_node in self.initial_node_set:
            input_node.add_upstream_node(*upstreams)

    def _detect_cycles(self, upstreams, downstreams):
        downstream_set = set()
        upstream_set = set()
        for node in downstreams:
            downstream_set = downstream_set.union(node.downstream_set)

        for node in upstreams:
            upstream_set = upstream_set.union(node.upstream_set)

        common_nodes = downstream_set.intersection(upstream_set)

        if common_nodes:
            msg = (
                '\n\nLoop detected in consecutor graph.'
                '  Node(s) {} encountered twice.'
            ).format(common_nodes)
            raise ValueError(msg)


    def __ror__(self, other):
        """
        """
        if isinstance(other, BaseNode):
            other = [other]

        self.connect_inputs(*other)
        out = list(self.terminal_node_set)
        #print('{} | {} --> {}'.format(other, self, out))
        return out[0] if len(out) == 1 else out

    @property
    def downstream(self):
        return self._downstream_nodes[0] if self._downstream_nodes else None

    @property
    def upstream(self):
        return self._upstream_nodes[0] if self._upstream_nodes else None

    def add_downstream_node(self, *other_nodes):
        #self._downstream_nodes.extend(other_nodes)
        for other in other_nodes:
            for init_node in other.initial_node_set:
                self._downstream_nodes.append(init_node)
                init_node._upstream_nodes.append(self)
                #print('add_downstream:  {}'.format(dict(src=self.name, dst=init_node.name, dir='forward')))
                self.edge_kwargs_list.append(
                    dict(src=self.name, dst=init_node.name, dir='forward'))

    def add_upstream_node(self, *other_nodes):
        for init_node in self.initial_node_set:
            for other in other_nodes:
                #if other.name == 'producer':
                init_node._upstream_nodes.append(other)
                other._downstream_nodes.append(init_node)
                #print('{}, add_upstream:  {}'.format(self, dict(src=other.name, dst=init_node.name, dir='forward')))
                self.edge_kwargs_list.append(
                    dict(src=other.name, dst=init_node.name, dir='forward'))

    def draw_pdf(self, file_name):
        # define a function to map over all nodes to aggreate viz kwargs
        def collect_kwargs(node, node_kwargs_list=None, edge_kwargs_list=None):
            node_kwargs_list.append(node.node_kwargs)
            edge_kwargs_list.extend(node.edge_kwargs_list)

        # gather the kwargs for creating the visualization
        node_kwargs_list, edge_kwargs_list = [], []

        self.apply_to_all_members(
            collect_kwargs, node_kwargs_list=node_kwargs_list,
            edge_kwargs_list=edge_kwargs_list
        )

        # doing import inside method so that pydot dependency is optional
        try:
            import pydot_ng as pydot
        except ImportError:
            raise ImportError(
                '\n\npydot-ng must be installed if you want to draw graphs')

        graph = pydot.Dot(graph_type='graph')
        for node_kwargs in node_kwargs_list:
            graph.add_node(pydot.Node(**node_kwargs))
        for edge_kwargs in edge_kwargs_list:
            graph.add_edge(pydot.Edge(**edge_kwargs))

        graph.write_pdf(file_name)


    @property
    def terminal_node_set(self):
        terminals = set()
        for downstream in self._downstream_nodes:
            terminals = terminals.union(downstream.terminal_node_set)
        if len(terminals) == 0:
            terminals = {self}
        return terminals

    @property
    def initial_node_set(self):
        initials = set()
        for upstream in self._upstream_nodes:
            initials = initials.union(upstream.initial_node_set)
        if len(initials) == 0:
            initials = {self}
        return initials

    @property
    def upstream_set(self):
        upstreams = {self}
        for upstream in self._upstream_nodes:
            upstreams = upstreams.union(upstream.upstream_set)
        return upstreams

    @property
    def downstream_set(self):
        downstreams = set()
        for downstream in self._downstream_nodes:
            downstreams = downstreams.union(downstream.downstream_set)
        downstreams = downstreams.union({self})
        return downstreams


    @property
    def dag_members(self):
        return self.downstream_set.union(self.upstream_set)

    def apply_to_all_members(self, func, *args, **kwargs):
        """
        func(node, *args, **kwargs)
        """
        for node in self.dag_members:
            func(node, *args, **kwargs)

    def new_item(self, anchor=None, value=None):
        if self.consecutor is None:
            raise ValueError(
                'You must run this node in a consecutor to create items')
        return self.consecutor._new_item(anchor, value)


    async def complete(self):
        for node in self.initial_node_set:
            await node._is_complete()

    async def _is_complete(self):
        if self._queue.qsize() > 0:
            await self._queue.join()
        await asyncio.gather(*[n._is_complete() for n in self._downstream_nodes])

    async def add_to_queue(self, item):
        await asyncio.Task(self._queue.put(item))

    async def write_output(self, name, item):
        if self.consecutor is None:
            raise ValueError(
                'You must run this node in a consecutor to write output')
        if name not in self.consecutor._allowed_output_names:
            msg = (
                'Unrecognized output name {}.'
                ' Allowed output names are {}.'
            ).format(name, sorted(consecutor._allowed_output_names))
            raise ValueError(msg)
        self.consecutor._output_list_named[name].append(item)

    async def push(self, item):
        if self.downstream:
            await self.downstream.add_to_queue(item)

    async def start(self):
        sentinal_count = 0
        while True:
            item = await self._queue.get()
            if isinstance(item, EndSentinal):
                sentinal_count += 1
                if sentinal_count == len(self._upstream_nodes):
                    for downstream in self._downstream_nodes:
                        await downstream.add_to_queue(item)
                    self._queue.task_done()
                    break
                else:
                    self._queue.task_done()
            else:
                try:
                    await self.process(item)
                    self._queue.task_done()
                except:
                    self._queue.task_done()
                    print('Error in {}'.format(self.name))
                    if self._log_errors:
                        log_errors(sys.exc_info(), node=self)

    def get_starts(self):
        def gather_starts(node, starts=None):
            starts.append(node.start())

        starts = []
        self.apply_to_all_members(gather_starts, starts=starts)
        return starts

class EndSentinal:
    def __str__(self):
        return 'sentinal'
    def __repr__(self):
        return self.__str__()


class ManualProducerNode(BaseNode):
    def __init__(self, *args, **kwargs):
        super(ManualProducerNode, self).__init__(*args, **kwargs)

    def produce_from(self, iterable):
        self.iterable = iterable

    async def start(self):
        if not self.downstream:
            raise ValueError(
                'Can\'t start a producer without something to consume it')
        for value in self.iterable:
            await self.downstream.add_to_queue(value)
        await self.downstream.add_to_queue(EndSentinal())
        await self.complete()
        self._loop.stop()

    def add_to_queue(self):
        raise NotImplementedError('Producers don\'t have send methods')


class BranchingNode(BaseNode):
    def __init__(self, *args, **kwargs):
        super(BranchingNode, self).__init__(*args, **kwargs)
        if 'name' not in kwargs:
            raise ValueError('branching nodes require names')
        self.name = '{}__broadcaster'.format(kwargs['name'])
        self.node_kwargs = dict(name=self.name, shape='rectangle')

    def set_routing_function(self, func):
        if func.__class__.__name__ == 'function':
            self.name =  self.name.replace(
                'broadcaster','{}'.format(func.__name__))
        else:
            self.name =  self.name.replace(
                'broadcaster','{}__router'.format(func.__class__.__name__))

        self.node_kwargs = dict(name=self.name, shape='rectangle')
        self._routing_function = func

    async def process(self, item):
        if self._routing_function:
            index = self._routing_function(item)
            if index > len(self._downstream_nodes) - 1:
                raise ValueError(
                    'Routing function provided invalid route')
            await asyncio.Task(
                self._downstream_nodes[index].add_to_queue(item))
        else:
            queue_tasks = [
                asyncio.Task(
                    node.add_to_queue(item)) for node in self._downstream_nodes
                ]
            await asyncio.gather(*queue_tasks)


class ComputeNode(BaseNode):
    def __init__(self, *args, **kwargs):
        super(ComputeNode, self).__init__(*args, **kwargs)

    async def make_job(self, function, *args, **kwargs):
        return await make_job(function, self, *args, **kwargs)

    async def exececute_in_parallel(self, *tasks, log_errors=True):
        """
        may want to take log_errors from a class variable instead of
        a function argument
        """
        futures = await asyncio.gather(*tasks)
        results = []
        for result in futures:
            results.append(await result)
        return results


    async def process(self, item):
        raise NotImplementedError('You must override the process method')



##############################################################################
class Preprocessor(ComputeNode):
    def __init__(self, *args, **kwargs):
        super(Preprocessor, self).__init__(*args, **kwargs)

    async def process(self, item):
        item = [item, self.name]
        print(item)
        await self.push(item)
        #await self.write_output('rob', ('out', item))

class Even(ComputeNode):
    def __init__(self, *args, **kwargs):
        super(Even, self).__init__(*args, **kwargs)

    async def process(self, item):
        item = [item, self.name]
        print(item)
        await self.push(item)


class Odd(ComputeNode):
    def __init__(self, *args, **kwargs):
        super(Odd, self).__init__(*args, **kwargs)

    async def process(self, item):
        item = [item, self.name]
        print(item)
        await self.push(item)

class Threes(ComputeNode):
    def __init__(self, *args, **kwargs):
        super(Threes, self).__init__(*args, **kwargs)

    async def process(self, item):
        item = [item, self.name]
        print(item)
        await self.push(item)

class Fours(ComputeNode):
    def __init__(self, *args, **kwargs):
        super(Fours, self).__init__(*args, **kwargs)

    async def process(self, item):
        item = [item, self.name]
        print(item)
        await self.push(item)


class Pass(ComputeNode):
    def __init__(self, *args, **kwargs):
        super(Pass, self).__init__(*args, **kwargs)

    async def process(self, item):
        if isinstance(item, list):
            item = [item[0], item[1:] + [self.name]]
        else:
            item = [item, self.name]
        await self.push(item)


class Printer(ComputeNode):
    def __init__(self, *args, **kwargs):
        super(Printer, self).__init__(*args, **kwargs)

    async def process(self, item):
        item = [item, self.name]
        print(item)

class Nothing(ComputeNode):
    def __init__(self, *args, **kwargs):
        super(Nothing, self).__init__(*args, **kwargs)

    async def process(self, item):
        pass


if __name__ == '__main__':

    def n_router(factor, item):
        if item[0] % factor == 0:
            return 0
        else:
            return 1

    def my_router(item):
        if item[0] % 3 == 0:
            return 0
        else:
            return 1

    def twos_router(item):
        return n_router(2, item)

    def threes_router(item):
        return n_router(3, item)

    def fours_router(item):
        return n_router(4, item)


    producer = ManualProducerNode(name='producer')
    by_two = Pass('by_two')
    not_by_two = Pass('not_by_two')
    by_three = Pass('by_three')
    not_by_three = Pass('not_by_three')
    by_four = Pass('by_four')
    not_by_four = Pass('not_by_four')
    pre = Pass('pre')
    printer = Printer('printer')
    post_two = Pass('post_two')
    post_three = Pass('post_three')

    producer | pre | [
        by_two, not_by_two, twos_router
    ] | post_two | [
        by_three, not_by_three, threes_router
    ] | post_three | [
        by_four, not_by_four, fours_router
    ] | printer






    #pre = Pass('pre')
    #a = Pass('a')
    #b = Pass('b')
    #c = Pass('c')
    #d = Pass('d')
    #e = Pass('e')
    #f = Pass('f')
    #g = Pass('g')
    #h = Pass('h')
    #i = Pass('i')
    #j = Pass('j')
    #k = Pass('k')
    #m = Printer('m')
    #producer | a | [
    #    b,
    #    c | [
    #            e,
    #            f  | [d, g, h, k, my_router] | i
    #    ] | j
    #] | m



    producer.draw_pdf('cons.pdf')





    #producer | Pass('pre') | [
    #    Pass(name='by_two'),
    #    Pass(name='other_than_two'),
    #    twos_router,
    #] | Pass(name='after_two') |  [
    #    Pass(name='by_three'),
    #    Pass(name='other_than_three'),
    #    threes_router,
    #] | Pass(name='after_three') |[
    #    Pass(name='by_fours'),
    #    Pass(name='other_than_four'),
    #    fours_router,
    #] | Printer('printer')



    producer.produce_from(range(13))
    master = asyncio.gather(*producer.get_starts())


    loop = asyncio.get_event_loop()
    asyncio.ensure_future(master)
    loop.run_forever()

    #producer.draw

    #print()
    #print()
    #for node in producer.dag_members:
    #    print(node)
    #print()
    #print()
    #for node in producer.initial_node_set:
    #    print(node)
    #print()
    #print()
    #for node in producer.terminal_node_set:
    #    print(node)


#if __name__ == '__main__':
#    producer = ManualProducerNode(name='producer')
#    n_comps = 2
#    parent = producer
#    for nn in range(n_comps):
#        parent = MyComputeNode(upstream=parent, name='comp{:02d}'.format(nn + 1))
#
#    producer.produce_from(range(1))
#    master = asyncio.gather(*producer.get_starts())
#
#
#    loop = asyncio.get_event_loop()
#    asyncio.ensure_future(master)
#    loop.run_forever()


