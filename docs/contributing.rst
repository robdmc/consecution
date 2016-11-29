Contributing
============

Running the tests
-----------------

To get the source source code and run the unit tests


Code Quality
------------

For code quality, please run flake8


Code Styling
------------
Please arrange imports with the following style

.. code-block:: python

    # Standard library imports
    import os

    # Third party package imports
    from mock import patch
    from django.conf import settings

    # Local package imports
    from brain.version import __version__

Please follow `Google's python style`_ guide wherever possible.

.. _Google's python style: http://google-styleguide.googlecode.com/svn/trunk/pyguide.html

Building the docs
-----------------

When in the project directory::

    $ python setup.py build_sphinx
    $ open docs/_build/html/index.html

