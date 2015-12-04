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
and maintaining a java-based project.  It would b really nice to have a
python-only implementation of the stream processing abstraction.  Consecution has
been designed to fill this void.

What is Consecution
---
* A robust stream-processing python library inspired by Apache Storm
* A clean, simple abstraction for pipe-lined data processing in python
* A good solution for creating real-time ETL systems
* Accepts streams of data from network connections, database cursors, or stdin.
* Guarentees that each item introduced to the system will be completely
  processed.
* Operates concurrently in either single-thread, multi-thread, or multi-process
  modes.




The first step to using consecution is to sketch out a pipeline





Current Stage of Developement
----
I am still in the very early stages of figuring out how to set everything
up.  I pushed this featureless package to pypi just to reserve the name.
