
This Repository is highly experimental and not ready for public consumption
===
It is basically my thought process on creating a python tool that will make ETL type tasks much easer.

Right now this README file is as much a brainstorm for myself as anything else.  Read at your own risk


Consecution
===

What is Consecution?
---
* A easy-to-use pipeline abstraction inspired by <a href="http://storm.apache.org/releases/current/Tutorial.html"> Apache Storm Topologies</a>
* Designed to simplify building ETL pipelines that are robust, and easy to test
* You define simple processing nodes, wire them together into a DAG, and feed the input node with an iterable
* Synchronous, single-process execution designed to run efficiently on a single core
* Efficient pure-python implementation with optional requirements needed only for graph visualization
* Written with 100% test coverage

Introduction
---
According to Wikipedia,

> The concept of pipelines was invented by Douglas McIlroy at Unix's ancestral home of Bell Labs, prior to the actual
> invention of the operating system, and implemented in Unix at his insistence, shaping its toolbox philosophy.

Consecution brings the pipeline design pattern to Python.  It lets you easily create and execute complex,
directed-graph pipelines in Python.  It is a pip-installable, and pure python.

Perhaps the best way to explain consecution is to show a simple, contrived example of a pipeline that computes the word
and letter entropy for the content in a batch of files.

```python
from future import print_function
import sys
import glob
from consecution import Node, Pipeline
from math import log

# Define several nodes to use as pipeline components

class LinesFromFileName(Node):
    """
    A class to extract lines from a file.  The .push() method will send
    its argument to all downstream nodes directly connected to this one.
    The .process() method is called once for each item pushed to the node.
    """
    def process(self, file_name):
        with open(file_name) as file:
            for line in file:
                self.push(line)

class WordsFromLine(Node):
    """
    A class to extract words from a line.  The if statement in this node
    filters the output so that only lines with words are processed.
    """
    def process(self, line):
        line = line.strip()
        if line:
            for word in line.split():
                self.push(word)

class LettersFromWord(Node):
    """
    A class to extract letters from a word
    """
    def process(self, word):
        for letter in word:
            self.push(letter)


class Entropy(Node):
    """
    A class to compute the Shannon entropy over a collection of items.
    This node uses a structure inspired by the BEGIN{} {} END{} directives
    in awk.
    """
    def begin(self):
        self.item_counts = {}
        self.total_items = 0

    def process(self, item):
        count = self.item_counts.get(item, 0)
        self.item_counts[item] = count + 1
        self.total_items += 1

    def end(self):
        # compute probbilities
        probabilities = [
            float(count) / self.total_items for count in self.item_counts.values()
        ]
        # compute shannon entropy from probabilities
        entropy = sum([-p * log(p) for p in probabilities])

        self.push({'name': self.name, 'entropy': entropy}})

class Printer(Node):
    """
    A simple node for printing results
    """
    def process(self, item):
        print('Entropy for {name} is {entropy}'.format(**item))

# Create instances of nodes so that they can be wired together into a pipeline
lines_frome_filename = LinesFromFileName(name='lines_from_file_name')
words_from_line = WordsFromLine(name='words_from_line')
letters_from_word = LettersFromWord(name='letters_from_word')
word_entropy = Entropy(name='word_entropy')
letter_entropy = Entropy(name='letter_entropy')
printer = Printer(name='printer')


# Wire up the nodes into a pipeline.  There are a couple different ways to do this.  This example
# illustrates the intuitive mini-language that consecution can use to create graphs.  The pipe operator is used
# just as it would be in bash to connect nodes.  Piping to a list of nodes broadcasts to each node (or branch)
# in the list.  Routing is also possible, but not demonstrated here.  Piping from a list to a node merges input
# from all nodes/branches from the list into the destination node.
pipeline = Pipeline(
    lines_from_file_names | words_from_line | [
        word_entropy,
        letters_from_word | letter_entropy
    ] | printer
)

# visualize the pipeline (requires the pydot2 pakage)
pipeline.visualize(kind='png')

# feed the pipeline an iterable
pipeline.consume(glob.glob('./*.txt'))
```


Why Consecution
---

Avid Python users can easily create tools that read data from stdin and send processed output on stdout.  These tools
are easily chained together in bash pipelines. Tools like <a href="https://github.com/robdmc/pandashells">
Pandashells</a> make doing this even more convenient.

The unix pipeline workflow, however, comes at a cost when building production systems.  If one process raises an error,
the entire pipeline fails. Obtaining reliable and useful stack traces for what went wrong can also be annoying.

It would be great if there was a way to implement the pipeline pattern in Python without resorting to system pipes.
Functional libraries like  <a href="https://github.com/pytoolz/toolz"> toolz </a> help with composing functions and
tools like <a href="http://dask.pydata.org/en/latest/"> Dask </a> and <a
href="http://deeplearning.net/software/theano/"> Theano</a> provide different approaches for creating and executing
computation graphs.

What's missing, however, is a tool for creating pipelines &mdash; or more precicely &mdash; directed-graphs of processing nodes.
Ideally the tool would be like a limited version of <a href="http://storm.apache.org/"> Apache Storm</a>.  It would
incorporate a simplified version of the topology abstraction from Storm and create a syncrhonous, single-threaded
execution strategy.

I can hear you saying.  "But this will not scale well for big data."  My response would be that you don't actually have
big data.  And if you do, then you are probably better off using tools like Kafa, Storm, Hadoop, etc. that have
been designed for scalability.  Consecution has been designed for the much more common case where you can handle
everything on a single core.

What is Consecution?
---
* A robust stream-processing python library inspired by Apache Storm
* A clean, simple abstraction for pipe-lined data processing in python
* A good solution for creating real-time ETL systems
* Accepts streams of data from network connections, database cursors, or stdin.
* Guarentees that each item introduced to the system will be completely
  processed even if process dies and is restarted.
* Operates concurrently in either single-thread, multi-thread, or multi-process
  modes.

Here is an example of a simple pipeline that will calculate all distances
between the ten busiest airports in the United States.

```bash
air_port_list | generate_all_combinations | geocode_adresses \
              | compute_distances | broadcast(databases_writer, file_writer)
```

Ideas for other streams.
Deductions from your paycheck.  Make stream of dollar for dollar. Make different
branches for each deduction and join them back together.

Amortized mortage.  360 payments of 1000 dollars.  Split off tax and insurance to
their own aggregators.  Initialize principal calculator with initial mortgage.
Each tuple get split up into two streams -- amount paid to interest and amount
paid to principal.  Interest gets split to tax refunder. All nodes get joined to
master aggregator.

Or maybe compounded investment with a monthly fee.  Payment comes in, fee gets
stripped out and aggregated, capital gets updated and splits off interest to its
own aggregator. 

Maybe a simple budget calculator.  Dollar comes in. Percent saving split off
from top.  Rent aggregates till full.  Food aggregates till full.

Let's say you've started a company that is now profitable and you and your
partner are starting to extract a share of the revenue.

Dollar comes in and is tagged with total revenue.  This gets routed to either
operating budget or profit distribution.  Goes through two additional nodes, one
for you, one for your partner which add  additional tuples of tagged takes.
Have a broadcaster with one leg to company aggregator and other leg to
filter/router between you and your parnter's aggregator as well as total revenue
aggregator. I LIKE THIS SCENARIO. 


#Types of Producer Nodes
Maybe define producers with an argument
```python
Producer(kind=pipe|tcp|http|manual|interval|scheduled, wait=timedelta, jitter=timedelta, cron_string)
```

Or maybe there are two types of producers

```python
SourcedProducer(kind=pipe|tcp|http|generator|pusher)

class TimedProducer
    def __init__(self, kind=interval|scheduled, wait=timedelta, jitter=timedelta, cron_string):
        pass
    
    def process(self):
        item = your_code_here()
        self.downstream.send(item)
```


Types of Utility Nodes
---
* Broadcast([node-list]):  
* Rout([node-list], rout-func=round-robin)
* Merge([node-list])
* Chunk(batch-by=func-or-int)


#Robustness
* Non-robust:  no tuple tracking whatsoever
* Confimation-only: Informs whether or not all tuples have been processed,
                    but no information about which tuple(s) failed
* Tracking-only: Keeps track of last N failed tuples, but does nothing else
* Robust: Replays failed tuples through the system up to N times.

Maybe there is some kind of mechanism for a consecutor to route failed
items to a specified location.  It might be nice to provide an abstraction
for this.


#Composition
Here are some thoughts on how to compose nodes and consecutors.

##Within consecutor composition

```python
branch1 = node1 | node2
branch2 = node3 | node4
producer | broadcast(branch1, branch2)
dag = merge(branch1, branch2) | node5
```

Or equivalently (if operator precedence pans out) 

```python
dag = producer < [
    node1 | node2, 
    node3 | node4,
] > node5
```

Maybe this for routing

```python
branch1 = node1 | node2
branch2 = node3 | node4
producer | route(func, branch1, branch2)
dag = merge(branch1, branch2) | node5
```

Or equivalently (if operator precedence pans out) 

```python
dag = producer < [
    route_func
    node1 | node2, 
    node3 | node4,
] > node5
```



##Between consecutor composition
Maybe the graph expressions above create objects of a Dag class, which may or
may not be the same thing as a Node class.

And then maybe you create consecutors like this.

```python
consecutor = Consecutor(dag)
```

Or, equivalently,

```python
consecutor = Consecutor(
  producer < [
      route_func
      node1 | node2, 
      node3 | node4,
  ] > node5,
  *args, **kwargs
)
```

Hmmm...  Maybe a consecutor should never include a producer.  Maybe producers
should be wired up to consecutors.  So it would be something like

```python
consecutor = Consecutor(
  node0 < [
      route_func
      node1 | node2, 
      node3 | node4,
  ] > node5,
  *args, **kwargs
)

producer | consecutor
```

Maybe consecutors can have named producers for their output.

```python
cons.output['a'] < [cons2.output['a'], cons3.output['b']] > cons4.output['a'] | cons5
```

It would be cool if these outputs could be either async or blocking.

The reason I want different levels of abstraction between nodes and consecutors
is that I want consecutors to have the notion of transaction-like guarenteed
processing.  No such guarentee exists between consecutors.


Maybe the nodes allow for writing to consecutor output.

Also.  Maybe there is some sentinal that can be sent between consecutors to
indicate that a batch has completed.  Not sure if this would be useful.

```python
class MyNode(Node):
    def __init__(self):
        self.add_async_output('my_output')

    def processes(item):
        if condition_true:
            self.async_output['my_output'].send(item)
```

Then a consecutor will search all nodes for outputs and and them to is output dict.
































