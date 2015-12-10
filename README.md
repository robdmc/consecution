Consecution
===

Introduction
---
The unix work flow of piping data between small, specialized programs has proven
to be extremely robust.  User who adopt this work flow do so by conceptualizaing
their computation as a stream of data flowing through a series (or
"consecution") of processing nodes.  Stream processing frameworks like <a
href="http://storm.apache.org/">Apache Storm</a> expand on this process by
creating an entire network of processing nodes where data flows in only one
direction from inputs to outputs and never loops back.  Apache storm is an
amazing project with unmatched robustness and scalability.  However, for the
python programmer, its use requires the inconveniece of installing, configuring,
and maintaining a java-based project.  It would be really nice to have a
python-only implementation of the stream processing abstraction.  Consecution has
been designed to meet these requirements.

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
































