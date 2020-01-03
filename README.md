Consecution
===
[![Build Status](https://travis-ci.org/robdmc/consecution.svg?branch=develop)](https://travis-ci.org/robdmc/consecution)
[![Coverage Status](https://coveralls.io/repos/github/robdmc/consecution/badge.svg?branch=develop)](https://coveralls.io/github/robdmc/consecution?branch=add_docs)

Introduction
---
Consecution is:
  * An easy-to-use pipeline abstraction inspired by <a href="http://storm.apache.org/releases/current/Tutorial.html"> Apache Storm Topologies</a>
  * Designed to simplify building ETL pipelines that are robust and easy to test
  * A system for wiring together simple processing nodes to form a DAG, which is fed with a python iterable
  * Built using synchronous, single-threaded execution strategies designed to run efficiently on a single core
  * Implemented in pure-python with optional requirements that are needed only for graph visualization
  * Written with 100% test coverage

Consecution makes it easy to build systems like this.

![Output Image](/images/etl_example.png?raw=true "ETL Example")


Installation
---
Consecution is a pure-python package that is simply installed with pip.  The only non-essential
requirement is the 
<a href="http://www.graphviz.org/">Graphviz</a> system package, which is only needed if you want to create
graphical representations of your pipeline.

<pre><code><strong>[~]$ pip install consecution</strong></code></pre>

Docker
---
If you would like to try out consecution on docker, check out consecution from github and navigate to the
`docker/` subdirectory.  From there, run the following.

* Build the consecution image: `docker_build.sh`
* Start a container: `docker_run.sh`
* Once in the container, run the example: `python simple_example.py`


Quick Start
---
What follows is a quick tour of consecution.  See the <a
href="http://consecution.readthedocs.io/en/latest/">API documentation</a> for
more detailed information.

### Nodes
Consecution works by wiring together nodes.  You create nodes by inheriting from the
`consecution.Node` class.  Every node must define a `.process()` method.  This method
contains whatever logic you want for processing single items as they pass through your
pipeline.  Here is an example of a node that simply logs items passing through it.
```python
from consecution import Node

class LogNode(Node):
    def process(self, item):
        # any logic you want for processing single item 
        print('{: >15} processing {}'.format(self.name, item))

        # send item downstream
        self.push(item)
```
### Pipelines
Now let's create a pipeline that wires together a series of these logging nodes.
We do this by employing the pipe symbol in  much the same way that you pipe data
between programs in unix.  Note that you must name nodes when you instantiate
them.
```python
from consecution import Node, Pipeline

# This is the same node class we defined above
class LogNode(Node):
    def process(self, item):
        print('{} processing {}'.format(self.name, item))
        self.push(item)

# Connect nodes with pipe symbols to create pipeline for consuming any iterable.
pipe = Pipeline(
    LogNode('extract') | LogNode('transform') | LogNode('load')
)
```
At this point, we can visualize the pipeline to verify that the topology is
what we expect it to be.  If you Graphviz installed, you can now simply type
one of the following to see the pipeline visualized.
```python
# Create a pipeline.png file in your working directory
pipe.plot()  

# Interactively display the pipeline visualization in an IPython notebook
# by simply making the final expression in a cell evaluate to a pipeline.
pipe
```
The plot command should produce the following visualization.

![Output Image](/images/etl1.png?raw=true "Three Node ETL Example")

If you don't have Graphviz installed, you can print the pipeline
object to get a text-based visualization.
```python
print(pipe)
```
This represents your pipeline as a series of pipe statements showing
how data is piped between nodes.
```
Pipeline
--------------------------------------------------------------------
  extract | transform
transform | load
--------------------------------------------------------------------
```


We can now process an iterable with our pipeline by running
```python
pipe.consume(range(5))
```
which will print the following to the console.
```
   extract processing 0
 transform processing 0
      load processing 0
   extract processing 1
 transform processing 1
      load processing 1
   extract processing 2
 transform processing 2
      load processing 2
```

### Broadcasting
Piping the output of a single node into a list of nodes will cause the single
node to broadcast its pushed items to every item in the list.  So, again, using
our logging node, we could construct a pipeline like this:
```python
from consecution import Node, Pipeline

class LogNode(Node):
    def process(self, item):
        print('{} processing {}'.format(self.name, item))
        self.push(item)

# pipe to a list of nodes to broadcast items
pipe = Pipeline(
    LogNode('extract') 
    | LogNode('transform') 
    | [LogNode('load_redis'), LogNode('load_postgres'), LogNode('load_mongo')]
)
pipe.plot()
pipe.consume(range(2))
```
The plot command produces this visualization

![Output Image](/images/broadcast.png?raw=true "Broadcast Example")

and consuming `range(2)` produces this output
```
      extract processing 0
    transform processing 0
   load_redis processing 0
load_postgres processing 0
   load_mongo processing 0
      extract processing 1
    transform processing 1
   load_redis processing 1
load_postgres processing 1
   load_mongo processing 1
```

### Routing
If you pipe to a list that contains multiple nodes and a single callable, then
consecution will interpret the callable as a routing function that accepts a
single item as its only argument and returns the name of one of the nodes in the
list.  The routing function will direct the flow of items as illustrated below.
```python
from consecution import Node, Pipeline

class LogNode(Node):
    def process(self, item):
        print('{: >15} processing {}'.format(self.name, item))
        self.push(item)
        
def parity(item):
    if item % 2 == 0:
        return 'transform_even'
    else:
        return 'transform_odd'

# pipe to a list containing a callable to achieve routing behaviour
pipe = Pipeline(
    LogNode('extract') 
    | [LogNode('transform_even'), LogNode('transform_odd'), parity] 
)
pipe.plot()
pipe.consume(range(4))
```
The plot command produces the following pipeline

![Output Image](/images/routing.png?raw=true "Routing Example")

and consuming `range(4)` produces this output
```
        extract processing 0
 transform_even processing 0
        extract processing 1
  transform_odd processing 1
        extract processing 2
 transform_even processing 2
        extract processing 3
  transform_odd processing 3
```


### Merging
Up to this point, we have the ability to create processing trees where nodes
can either broadcast to or route between their downstream nodes.  We can,
however, do more then this and create DAGs (Directed-Acyclic-Graphs).  Piping
from a list back to a single node will merge the output of all nodes in the
list together into the single downstream node like this.
```python
from consecution import Node, Pipeline

class LogNode(Node):
    def process(self, item):
        print('{: >15} processing {}'.format(self.name, item))
        self.push(item)
        
def parity(item):
    if item % 2 == 0:
        return 'transform_even'
    else:
        return 'transform_odd'

# piping from a list back to a single node merges items into downstream node
pipe = Pipeline(
    LogNode('extract') 
    | [LogNode('transform_even'), LogNode('transform_odd'), parity] 
    | LogNode('load')
)
pipe.plot()
pipe.consume(range(4))
```
The plot command produces the following pipeline

![Output Image](/images/dag.png?raw=true "DAG Example")

and consuming `range(4)` produces this output
```
        extract processing 0
 transform_even processing 0
           load processing 0
        extract processing 1
  transform_odd processing 1
           load processing 1
        extract processing 2
 transform_even processing 2
           load processing 2
        extract processing 3
  transform_odd processing 3
           load processing 3
```
### Managing Local State
Nodes are classes, and as such, you have the freedom to create any attribute you
want on a node.  You can actually define two additional methods on your nodes to
set up and tear down node-local state.  It is important to note the order of
execution here.  All nodes in a pipeline will execute their `.begin()` methods
in pipeline-order before any items are processed.  Each node will enter its
`.end()` method only after it has processed all items, and after all parent
nodes have finished their respective `.end()` methods.  Below, we've modified
our LogNode to keep a running sum of all items that pass through it and end by
printing their sum.
```python
from consecution import Node, Pipeline

class LogNode(Node):
    def begin(self):
        self.sum = 0
        print('{}.begin()'.format(self.name))

    def process(self, item):
        print('{: >15} processing {}'.format(self.name, item))
        self.sum += item
        self.push(item)

    def end(self):
        print('sum = {:d} in {}.end()'.format(self.sum, self.name))

# Identical pipeline to merge example above, but with modified LogNode
pipe = Pipeline(
    LogNode('extract') 
    | [LogNode('transform_even'), LogNode('transform_odd'), parity] 
    | LogNode('load')
)
pipe.consume(range(4))
```

Consuming `range(4)` produces the following output
```
extract.begin()
transform_even.begin()
transform_odd.begin()
load.begin()
        extract processing 0
 transform_even processing 0
           load processing 0
        extract processing 1
  transform_odd processing 1
           load processing 1
        extract processing 2
 transform_even processing 2
           load processing 2
        extract processing 3
  transform_odd processing 3
           load processing 3
sum = 6 in extract.end()
sum = 2 in transform_even.end()
sum = 4 in transform_odd.end()
sum = 6 in load.end()
```


### Managing Global State 
Every node object has a `.global_state` attribute that is shared globally across
all nodes in the pipeline.  The attribute is also available on the Pipeline
object itself.  The GlobalState object is a simple mutable python object whose
attributes can be mutated by any node.  It also remains accesible on the
Pipeline object after all nodes have completed.  Below is a simple example of
mutating and accessing global state.

```python
from consecution import Node, Pipeline, GlobalState

class LogNode(Node):
    def process(self, item):
        self.global_state.messages.append(
            '{: >15} processing {}'.format(self.name, item)
        )
        self.push(item)
        
# create a global state object with a messages attribute
global_state = GlobalState(messages=[])

# Assign the predefined global_state to the pipeline
pipe = Pipeline(
    LogNode('extract') | LogNode('transform') | LogNode('load'),
    global_state=global_state)
)
pipe.consume(range(3))

# print the content of the global state message list
for msg in pipe.global_state.messages:
    print msg
```

Printing the contents of the messages list produces
```
  extract processing 0
transform processing 0
     load processing 0
  extract processing 1
transform processing 1
     load processing 1
  extract processing 2
transform processing 2
     load processing 2
```

## Common Patterns
This section shows examples of how to implement some common patterns in
consecution.

### Map
Mapping with nodes is very simple. Just push an altered item downstream.
```python
from consecution import Node, Pipeline
class Mapper(Node):
    def process(self, item):
        self.push(2 * item)

class LogNode(Node):
    def process(self, item):
        print('{: >15} processing {}'.format(self.name, item))
        self.push(item)

pipe = Pipeline(
    LogNode('extractor') | Mapper('mapper') | LogNode('loader')
)

pipe.consume(range(3))
```
This will produce an output of
```
extractor processing 0
   loader processing 0
extractor processing 1
   loader processing 2
extractor processing 2
   loader processing 4
```

### Reduce
Reducing, or folding, is easily implemented by using the `.begin()`
and `.end()` methods to handle accumulated values.
```python
from consecution import Node, Pipeline
class Reducer(Node):
    def begin(self):
        self.result = 0
        
    def process(self, item):
        self.result += item
        
    def end(self):
        self.push(self.result)

class LogNode(Node):
    def process(self, item):
        print('{: >15} processing {}'.format(self.name, item))
        self.push(item)

pipe = Pipeline(
    LogNode('extractor') | Reducer('reducer') | LogNode('loader')
)

pipe.consume(range(3))
```
This will produce an output of
```
extractor processing 0
extractor processing 1
extractor processing 2
   loader processing 3
```

### Filter
Filtering is as simple as placing the push statement behind a conditional. All
items that don't pass the conditional will not be pushed downstream, and thus
silently dropped.
```python
from consecution import Node, Pipeline
class Filter(Node):
    def process(self, item):
        if item > 3:
            self.push(item)

class LogNode(Node):
    def process(self, item):
        print('{: >15} processing {}'.format(self.name, item))
        self.push(item)

pipe = Pipeline(
    LogNode('extractor') | Filter('filter') | LogNode('loader')
)

pipe.consume(range(6))
```
This produces an output of
```
extractor processing 0
extractor processing 1
extractor processing 2
extractor processing 3
extractor processing 4
   loader processing 4
extractor processing 5
   loader processing 5
```

### Group By
Consecution provides a specialized class you can inherit from to perform
grouping operations.  GroupBy nodes must define two methods: `.key(item)` and
`.process(batch)`.  The `.key` method should return a key from an item that is used
to identify groups.  Any time that key changes, a new group is initiated.  Like
Python's `itertools.groupby`, you will usually want the GroupByNode to process
sorted items.  The `.process` method functions exactly like the `.process`
method on regular nodes, except that instead of being called with items,
consecution will call it with a batch of items contained in a list.
```python
class LogNode(Node):
    def process(self, item):
        print('{: >15} processing {}'.format(self.name, item))
        self.push(item)

class Batcher(GroupByNode):
    def key(self, item):
        return item // 4
    
    def process(self, batch):
        sum_val = sum(batch)
        self.push(sum_val)
        
pipe = Pipeline(
    Batcher('batcher') | LogNode('logger') 
)

pipe.consume(range(16))
```
This produces an output of
```
logger processing 6
logger processing 22
logger processing 38
logger processing 54
```

### Plugin-Style Composition
Consecution forces you to think about problems in terms of how small processing
units are connected.  This separation between logic and connectivity can be
exploited to create flexible and reusable solutions.  Basically, you specify the
connectivity you want to use in solving your problem, and then plug in the
processing units later.  Breaking the problem up in this way allows you to swap
out processing units to acheive different objectives with the same pipeline.

```python
# This function defines a pipeline that can use swappable processing nodes.
# We don't worry about how we are going to do logging or aggregating.
# We just focus on how the nodes are connected.
def pipeline_factory(log_node, agg_node):
    pipe = Pipeline(
        log_node('extractor') | agg_node('aggregator') | log_node('result_logger')
    )
    return pipe


# Now we define a node for left-justified logging
class LeftLogNode(Node):
    def process(self, item):
        print('{: <15} processing {}'.format(self.name, item))
        self.push(item)

# And one for right-justified logging
class RightLogNode(Node):
    def process(self, item):
        print('{: >15} processing {}'.format(self.name, item))
        self.push(item)

# We can aggregate by summing
class SumNode(Node):
    def begin(self):
        self.result = 0
        
    def process(self, item):
        self.result += item
        
    def end(self):
        self.push(self.result)

# Or we can aggregate by multiplying
class ProdNode(Node):
    def begin(self):
        self.result = 1
        
    def process(self, item):
        self.result *= item
        
    def end(self):
        self.push(self.result)


# Now we plug in nodes to create a pipeline that left-prints sums
sum_pipeline = pipeline_factory(log_node=LeftLogNode, agg_node=SumNode)

# And a different pipeline that right prints products
prod_pipeline = pipeline_factory(log_node=RightLogNode, agg_node=ProdNode)

print 'aggregate with sum, left justified\n' + '-'*40
sum_pipeline.consume(range(1, 5))

print '\naggregate with product, right justified\n' + '-'*40
prod_pipeline.consume(range(1, 5))
```
This produces the following output
```
aggregate with sum, left justified
----------------------------------------
extractor       processing 1
extractor       processing 2
extractor       processing 3
extractor       processing 4
result_logger   processing 10

aggregate with product, right justified
----------------------------------------
      extractor processing 1
      extractor processing 2
      extractor processing 3
      extractor processing 4
  result_logger processing 24
```

# Aggregation Example
We end with a full-blown example of using a pipeline to aggregate data from a
csv file.  The data is contained in 
<a href="https://raw.githubusercontent.com/robdmc/consecution/master/sample_data.csv">
a csv file </a> that looks like this.

gender |age |spent
---    |--- |---
male   |11  |39.39
female |10  |34.72
female |15  |40.02
male   |19  |26.27
male   |13  |21.22
female |40  |23.17
female |52  |33.42
male   |33  |39.52
female |16  |28.65
male   |60  |26.74


Although there are much simpler ways of solving this problem, (e.g. with <a
href="https://github.com/robdmc/consecution/blob/master/pandashells.md">
Pandashells</a>)
we deliberately construct a complex topology just to illustrate how to achieve
complexity when it is actually needed.

The diagram below was produced from the code beneath it.  A quick glance at the
diagram makes it obvious how the data is being routed through the system.  The
code is heavily commented to explain features of the consecution toolkit.

![Output Image](/images/gender_age.png?raw=true "Gender Age Pipeline")

```python
from __future__ import print_function
from collections import namedtuple
from pprint import pprint
import csv
from consecution import Node, Pipeline, GlobalState

# Named tuples are nice immutable containers 
# for passing data between nodes
Person = namedtuple('Person', 'gender age spent')

# Create a pipeline that aggregates by gender and age
# In creating the pipeline we focus on connectivity and don't
# worry about defining node behavior.
def pipe_factory(Extractor, Agg, gender_router, age_router):
    # Consecution provides a generic GlobalState class.  Any object can be used
    # as the global_state in a pipeline, but the GlobalState object provides a
    # nice abstraction where attributes can be accessed either by dot notation
    # (e.g. global_state.my_attribute) or by dictionary notation (e.g.
    # global_state['my_attribute'].  Furthermore, GlobalState objects can be
    # instantiated with initialized attributes using key-word arguments as shown
    # here.
    global_state = GlobalState(segment_totals={})

    # Notice, we haven't even defined the behavior of these nodes yet.  They
    # will be defined later and are, for now, just passed into the factory
    # function as arguments while we focus on getting the topology right.
    pipe = Pipeline(
        Extractor('make_person') |
        [
            gender_router,
            (Agg('male') | [age_router, Agg('male_child'), Agg('male_adult')]),
            (Agg('female') | [age_router, Agg('female_child'), Agg('female_adult')]),
        ],
        global_state=global_state
    )

    # Nodes can be created outside of a pipeline definition
    adult = Agg('adult')
    child = Agg('child')
    total = Agg('total')

    # Sometimes the topology you want to create cannot easily be expressed
    # using the pipeline abstraction for wiring nodes together.  You can
    # drop down to a lower level of abstraction by explicitly wiring nodes 
    # together using the .add_downstream() method.
    adult.add_downstream(total)
    child.add_downstream(total)

    # Once a pipeline has been created, you can access individual nodes
    # with dictionary-like indexing on the pipeline.
    pipe['male_child'].add_downstream(child)
    pipe['female_child'].add_downstream(child)
    pipe['male_adult'].add_downstream(adult)
    pipe['female_adult'].add_downstream(adult)

    return pipe

# Now that we have the topology of our pipeline defined, we can think about the
# logic that needs to go into each node.  We start by defining a node that takes
# a row from a csv file and tranforms it into a namedtuple.
class MakePerson(Node):
    def process(self, item):
        item['age'] = int(item['age'])
        item['spent'] = float(item['spent'])
        self.push(Person(**item))

# We now define a node to perform our aggregations.  Mutable global state comes
# with a lot of baggage and should be used with care.  This node illustrates
# how to use global state to put all aggregations in a central location that
# remains accessible when the pipeline finishes processing.
class Sum(Node):
    def begin(self):
        # initialize the node-local sum to zero
        self.total = 0

    def process(self, item):
        # increment the node-local total and push the item down stream
        self.total += item.spent
        self.push(item)

    def end(self):
        # when pipeline is done, update global state with sum
        self.global_state.segment_totals[self.name] = round(self.total, 2)


# This function routes tuples based on their associated gender
def by_gender(item):
    return '{}'.format(item.gender)

# This function routes tuples based on whether the purchaser was an adult or
# child
def by_age(item):
    if item.age >= 18:
        return '{}_adult'.format(item.gender)
    else:
        return '{}_child'.format(item.gender)

# Here we plug our node definitions into our topology to create a fully-defined
# pipeline.
pipe = pipe_factory(MakePerson, Sum, by_gender, by_age)

# We can now visualize pipeline.
pipe.plot()

# Now we feed our pipeline with rows from the csv file
with open('sample_data.csv') as f:
    pipe.consume(csv.DictReader(f))

# The global_state is also available as an attribute on the pipeline allowing
# us to access it when the pipeline is finished.  This is a good way to "return"
# an object from a pipeline.  Here we simply print the result.
print()
pprint(pipe.global_state.segment_totals)
```

And this is the result of running the pipeline with the sample csv file.
```
{'adult': 149.12,
 'child': 164.0,
 'female': 159.98,
 'female_adult': 56.59,
 'female_child': 103.39,
 'male': 153.14,
 'male_adult': 92.53,
 'male_child': 60.61,
 'total': 313.12}
```

As illustrated in the <a
href="https://github.com/robdmc/consecution/blob/master/pandashells.md">
Pandashells</a> example, this aggregation is actually much more simple to
implement in Pandas.  However, there are a couple of important caveats.

The Pandas solution must load the entire csv file into memory at once.  If you
look at the pipeline solution, you will notice that each node simply increments
its local sum and passes the data downstream.  At no point is the data
completely loaded into memory.  Although the Pandas code runs much faster due to
the highly optimized vectorized math it employes, the pipeline solution can
process arbitrarily large csv files with a very small memory footprint.

Perhaps the most exciting aspect of consecution is its ability to create
repeatable and testable data analysis pipelines.  Passing Pandas Dataframes
through a consecution pipeline makes it very easy to encapsulate any analysis
into a well-defined, repeatable process where each node manipulates a dataframe
in its prescribed way. Adopting this structure in analysis projects will
undoubtedly ease the transition from analysis/research into production.

___
Projects by [robdmc](https://www.linkedin.com/in/robdecarvalho).
* [Pandashells](https://github.com/robdmc/pandashells) Pandas at the bash command line
* [Consecution](https://github.com/robdmc/consecution) Pipeline abstraction for Python
* [Behold](https://github.com/robdmc/behold) Helping debug large Python projects
* [Crontabs](https://github.com/robdmc/crontabs) Simple scheduling library for Python scripts
* [Switchenv](https://github.com/robdmc/switchenv) Manager for bash environments
