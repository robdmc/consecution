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





Current Stage of Developement
----
I am still in the very early stages of figuring out how to set everything
up.  I pushed this featureless package to pypi just to reserve the name.
