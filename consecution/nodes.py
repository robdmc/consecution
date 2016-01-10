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
        #return '<class {}> {}'.format(self.__class__.__name__, self.name)
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

    def connect_outputs(self, *downstreams):
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
            branching_node.connect_outputs(*downstream_nodes)
            self.connect_outputs(branching_node)

        out = list(self.terminal_node_set)
        return out[0] if len(out) == 1 else out


    #def __or__(self, other):
    #    """
    #    """
    #    # transform other into list of nodes
    #    if isinstance(other, BaseNode):
    #        downstream_elements = [other]
    #    elif isinstance(other, list):
    #        downstream_elements = other
    #    else:
    #        msg = (
    #            '\n\nError joining:\n'
    #            '{} | {}\n\n'
    #            'Nodes can only be joined with other nodes or lists of nodes'
    #            '\n\n'
    #        ).format(self, other)
    #        raise ValueError(msg)

    #    # separate node elements from routing function elements
    #    downstream_nodes = [
    #        el for el in downstream_elements if isinstance(el, BaseNode)]
    #    function_elements = [
    #        el for el in downstream_elements if hasattr(el, '__call__')]

    #    # run error checks against inputs to make sure joining makes sense
    #    if len(downstream_elements) != (
    #            len(downstream_nodes) + len(function_elements)):
    #        pass
    #        #print('\n\n' + '*'*80)
    #        #print(self)
    #        #print(other)
    #        #print(type(other))
    #        #print()
    #        #raise ValueError()

    #        #msg = '\n\nError joining:\n'
    #        #msg += '{} | {}\n\b'.format(self, other)
    #        #msg += 'Joins must be one-to-one, one-to-many, or many-to-one'
    #        #msg += '\n\n'
    #        #raise ValueError(msg)




    #        #raise ValueError(
    #        #    'Nodes can only be joined with other nodes or lists of '
    #        #    'nodes / routing callables.')
    #    if len(function_elements) > 1:
    #        raise ValueError(
    #            'You can\'t specify more than one routing function in a list')
    #    if len(downstream_nodes) == 0:
    #        raise ValueError(
    #            'You must specify at least one downstream node.')

    #    print('\nor with {} {}'.format(self, downstream_nodes))
    #    # if there are no branches, just add downstream node
    #    if len(downstream_nodes) == 1:
    #        self.add_downstream_node(*downstream_nodes)
    #        print('returning {} '.format(downstream_nodes[0]))
    #        return downstream_nodes[0]
    #    # otherwise add the appropriate branching node
    #    else:
    #        branching_node = BranchingNode(name=self.name)
    #        if function_elements:
    #            branching_node.set_routing_function(function_elements[0])
    #        self.add_downstream_node(branching_node)
    #        branching_node.add_downstream_node(*downstream_nodes)
    #        print('returning {} '.format(downstream_nodes))
    #        return downstream_nodes

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

    def connect_inputs(self, *upstreams):
        self.validate_inputs(upstreams)
        for upstream in upstreams:
            upstream.add_downstream_node(*list(self.initial_node_set))

    def __ror__(self, other):
        """
        """
        if isinstance(other, BaseNode):
            other = [other]
        self.connect_inputs(*other)
        return list(self.terminal_node_set)

    #def __ror__(self, other):
    #    """
    #    """
    #    # transform other into list of nodes
    #    if isinstance(other, BaseNode):
    #        upstream_nodes = [other]
    #    elif isinstance(other, list):
    #        upstream_nodes = other
    #    else:
    #        raise ValueError(
    #            'Nodes can only be joined with other nodes or lists of '
    #            'nodes.')

    #    if len(upstream_nodes) == 0:
    #        raise ValueError(
    #            'You must specify at least one upstream node.')

    #    self.add_upstream_node(*upstream_nodes)
    #    return self


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
                self.edge_kwargs_list.append(
                    dict(src=self.name, dst=init_node.name, dir='forward'))

    def add_upstream_node(self, *other_nodes):
        for init_node in self.initial_node_set:
            for other in other_nodes:
                #if other.name == 'producer':
                init_node._upstream_nodes.append(other)
                other._downstream_nodes.append(init_node)
                self.edge_kwargs_list.append(
                    dict(src=other.name, dst=init_node.name, dir='forward'))

    #def create_viz_node(self):
    #    self.node_kwargs_list.append(dict(name=self.name, shape='rectangle'))

    #def add_viz_upstream(self, *other_nodes):
    #    if self.pydot_node_class:
    #        for other_node in other_nodes:
    #            self.edge_kwargs_list.append(
    #                dict(other_node.name, self.name, dir='forward'))

    #def add_viz_downstream(self, *other_nodes):
    #    if self.pydot_node_class:
    #        for other_node in other_nodes:
    #            self.edge_kwargs_list.append(
    #                dict(self.name, other_node.name, dir='forward'))

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
        await asyncio.gather(*[n._queue.join() for n in self.dag_members])


    async def add_to_queue(self, item):
        #await self._queue.put(item)
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
        while True:
            item = await self._queue.get()
            if isinstance(item, EndSentinal):
                for downstream in self._downstream_nodes:
                    await downstream.add_to_queue(item)
                self._queue.task_done()
                break
            else:
                try:
                    await self.process(item)
                    self._queue.task_done()
                except:
                    self._queue.task_done()
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

    #def __init__(self, name='', log_errors=True, loop=None):
    #    super(ManualProducerNode, self).__init__(
    #        name='', log_errors=log_errors, loop=loop
    #    )

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
        #TODO: make a list of forbidden node names that includes "broadcast"
        # also include the name of routing function in pydot node
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
            #self.name =  '{}__router'.format(func.__class__.__name__)

        self.node_kwargs = dict(name=self.name, shape='rectangle')
        self._routing_function = func

    async def process(self, item):
        if self._routing_function:
            index = self._routing_function(item)
            if index > len(self._downstream_nodes) - 1:
                raise ValueError(
                    'Routing function provided invalid route')
            await self._downstream_nodes[index].add_to_queue(item)
        else:
            for downstream in self._downstream_nodes:
                await downstream.add_to_queue(item)


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

#class MyComputeNode(ComputeNode):
#    def __init__(self, *args, **kwargs):
#        super(MyComputeNode, self).__init__(*args, **kwargs)
#
#    async def process(self, item):
#
#        job1 = self.make_job(my_blocking_code1, self.name, item)
#        job2 = self.make_job(my_blocking_code1, self.name, item)
#
#        results = await self.exececute_in_parallel(job1, job2)
#        #for res in results:
#        #    print(res)
#
#        print(self.name, item)
#        await self.push(item)
#
#        """
#        Got decent error handling in the executed function.
#        Next step is to nicely handle errors in this process function
#        Maybe make the error logging a class-based thing.
#
#        Would like to see how things work for processes as well as threads
#        """

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
        #await self.push(item)


if __name__ == '__main__':

    def n_router(factor, item):
        if item[0] % factor == 0:
            return 0
        else:
            return 1

    twos_router = partial(n_router, 2)
    threes_router = partial(n_router, 3)
    fours_router = partial(n_router, 4)


    producer = ManualProducerNode(name='producer')
    #THE FOLLOWING GRAPH CONSTRUCT IS NOT WORKING AND I WANT IT TO

    #producer  | [
    #    Even(name='eve') | [Pass(name='pass')],
    #]
    #pre = Pass(name='pre')
    #eve = Pass(name='eve')
    #odd = Pass(name='odd')
    #passer_eve = Pass(name='passer_eve')
    #passer_odd = Pass(name='passer_odd')
    #post = Post(name='post')

    #pre = Pass('pre')
    #a = Printer('a')
    #b = Printer('b')

    ##I THINK THIS SHOULD WORK
    #producer | pre| [
    #    a,
    #    b
    #]


    ##I THINK THIS SHOULD WORK
    #producer | Pass('pre') | [
    #    Printer('a'),
    #    Printer('b')
    #] 

    pre = Pass('pre')
    a = Pass('a')
    b = Pass('b')
    c = Printer('c')
    d = Printer('d')
    e = Printer('e')


    ###I THINK THIS SHOULD WORK
    producer | pre| [
        a,
        b #| [c, d] #| e
    ] | Printer('printer')

    #for node in producer.dag_members:
    #    print(node, node._upstream_nodes, node._downstream_nodes)

    #sys.exit()

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


    producer.draw_pdf('cons.pdf')

    producer.produce_from(range(16))
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


