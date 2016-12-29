#!/usr/bin/env python

import io
import os
import re
from setuptools import setup, find_packages

file_dir = os.path.dirname(__file__)


def read(path, encoding='utf-8'):
    path = os.path.join(os.path.dirname(__file__), path)
    with io.open(path, encoding=encoding) as fp:
        return fp.read()


def version(path):
    """Obtain the packge version from a python file e.g. pkg/__init__.py
    See <https://packaging.python.org/en/latest/single_source_version.html>.
    """
    version_file = read(path)
    version_match = re.search(r"""^__version__ = ['"]([^'"]*)['"]""",
                              version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")


LONG_DESCRIPTION = """
Consecution is an easy-to-use pipeline abstraction inspired by
Apache Storm topologies.
"""

setup(
    name='consecution',
    version=version(os.path.join(file_dir, 'consecution', '__init__.py')),
    author='Rob deCarvalho',
    author_email='unlisted',
    description=('Pipeline Abstraction Library'),
    license='BSD',
    keywords=('pipeline apache storm DAG graph topology ETL'),
    url='https://github.com/robdmc/consecution',
    packages=find_packages(),
    long_description=LONG_DESCRIPTION,
    classifiers=[
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.5',
        'Topic :: Scientific/Engineering',
    ],
    extras_require={'dev': ['nose', 'coverage', 'mock', 'flake8', 'coveralls']},
    install_requires=['graphviz']
)
