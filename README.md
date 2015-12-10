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


Types of Producer Nodes
---
* Producer(kind='pipe'|'http'|'manual')

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

##option 1
first set of options

##option 2
second set of options
















