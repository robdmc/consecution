
This Repository is highly experimental and not ready for public consumption
===
It is basically my thought process on creating a python tool that will make ETL type tasks much easer.

Right now this README file is as much a brainstorm for myself as anything else.  Read at your own risk


Consecution
===

Introduction
---
Unix pipes excel at tying together single-purpose executables into very useful pipelines.  Tools like <a
href="https://github.com/robdmc/pandashells">Pandashells</a> make creating such pipelines with Python quite easy. These
pipelines are fantastic for quick analyses or ad-hoc ETL tasks.  They are not, however, as good for creating robust,
production-ready systems that are fully tested and easy to maintain.

Consecution was built to address this need.  It borrows the unix pipeline workflow and expands it to handle arbitrarily
complex networks of processing nodes that have been wired together to form a directed acyclic graph (DAG).

Functional libraries like <a href="https://github.com/pytoolz/toolz">toolz</a> can be used to compose functions into
pipelines, and tools like <a href="http://dask.pydata.org/en/latest/">Dask</a> and <a
href="http://deeplearning.net/software/theano/">Theano</a> provide different approaches for creating and executing
computation graphs.  What these tools lack, however, is a simple abstraction for wiring together processing nodes into a
computation graph that can be fed with a data like a pipeline.

Those familiar with <a href="http://storm.apache.org/">Apache Storm</a> will recognize what the Storm community calls a
"topology."  Consecution is a topology-inspired abstraction for Python.

What is Consecution?
---
* An easy-to-use pipeline abstraction inspired by <a href="http://storm.apache.org/releases/current/Tutorial.html"> Apache Storm Topologies</a>
* Designed to simplify building ETL pipelines that are robust and easy to test
* Simple processing nodes are wired together to form a DAG, which is fed with a python iterable
* Synchronous, single-threaded execution is designed to run efficiently on a single core
* Pure-python implementation with optional requirements that are needed only for graph visualization
* Written with 100% test coverage

Overview
---
The word <a href="http://www.dictionary.com/browse/consecution">"consecution"</a> refers to a logical sequence or
chain of reason, and quite accurately describes the idea of chaining together processing nodes into a directed acyclic
graph (DAG) for computation.

The way to think about consecution's work flow is to envision a single source of data broken up into individual little
chunks, which we will call items.  In practice these items are elements of a Python iterable.  This precession of
items are visualized as a data stream that can be split apart, recombined, and transformed through a network of simple
processing nodes arranged in an arbitrarily complex DAG.  The advantage of this design are that:
* Computations are more easily visualized making dependencies easy to understand, and systems easier to debug.
* Nodes are simple, small snippets of code designed to perform a single task with one input and one output.
* Nodes can optionally access a global mutable-state object, but robust designs will minimize this interaction thereby
  forcing loose coupling across the code-base.
* Complex logic can be achieved by either making the nodes themselves more complex, or by pushing that complexity into
  the topology of the graph by clever use of broadcast, routing and merging nodes.
* The single-input / single-output node structure makes testing very easy.


Perhaps the best way to fully grasp consecution is to consider a simple (although admittedly contrived) example.
Imagine you are given a list of files and your job is to compute the <a
href="https://en.wikipedia.org/wiki/Entropy_(information_theory)">Shannon Entropy</a> of the corpus of text contained
in the files.  You are to compute two entropies actually: One based on all the words in the file, and the other based
on all the characters in the file. This task is actually fairly straightforward to visualize with a flow chart, or
DAG, which is drawn here.

IMAGE IMBED HERE

This flowchart was actually drawn directly from the consecution code listed below.  Notice how simple each node is,
and how data flows through each node, one item at a time.  Also notice how each node is able to initialize, maintain,
and clean up its internal state.  Finally, notice how the mini-language for wiring nodes together actually has some
visual similarity to the DAG itself.



```python
from future import print_function
import sys
import glob
from consecution import Node, Pipeline
from math import log


class LinesFromFileName(Node):
    """
    A node to extract lines from a file.  The .push() method will send
    its argument to all downstream nodes directly connected to this one.
    The .process() method is called once for each item pushed to the node.
    """
    def process(self, file_name):
        with open(file_name) as file:
            for line in file:
                self.push(line)


class WordsFromLine(Node):
    """
    A node to extract words from a line.  The if statement in this node
    filters the output so that only lines with words are processed.
    """
    def process(self, line):
        line = line.strip()
        if line:
            for word in line.split():
                self.push(word)


class LettersFromWord(Node):
    """
    A node to extract letters from a word
    """
    def process(self, word):
        for letter in word:
            self.push(letter)


class Entropy(Node):
    """
    A node to compute the Shannon entropy over a collection of items.
    This node uses a structure inspired by the BEGIN{} {} END{} directives
    in awk. The .begin() method is run at node initialization, and the .end()
    method is run after the node has processed all items.
    """
    def begin(self):
        # initialize internal state
        self.item_counts = {}
        self.total_items = 0

    def process(self, item):
        # update internal state with item counts
        count = self.item_counts.get(item, 0)
        self.item_counts[item] = count + 1
        self.total_items += 1

    def end(self):
        # compute probbilities from counts
        probabilities = [
            float(count) / self.total_items for count in self.item_counts.values()
        ]

        # compute shannon entropy from probabilities
        entropy = sum([-p * log(p) for p in probabilities])

        # push shannon entropy downstream
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


# Wire up the nodes into a pipeline.  There are a couple different ways to do this.  This
# example illustrates the intuitive mini-language that consecution can use to create
# graphs.  The pipe operator is used to connect nodes just as it would be in bash to
# connect processes.  Piping to a list of nodes broadcasts to each node (or branch) in the
# list.  Routing is also possible, but not demonstrated here.  Piping from a list to a
# node merges the output from all nodes/branches from the list into the destination node.
pipeline = Pipeline(
    lines_from_file_names | words_from_line |
    [
        word_entropy,
        letters_from_word | letter_entropy
    ]
    | printer
)

# visualize the pipeline (requires the pydot2 pakage)
pipeline.visualize(kind='png')

# feed the pipeline with an iterable
pipeline.consume(glob.glob('./*.txt'))
```
