#!/usr/bin/env python

import os
from setuptools import setup, find_packages

fileDir = os.path.dirname(__file__)

LONG_DESCRIPTION = """
A concurrent stream processing framework for python.
"""

setup(
    name="consecution",
    version="0.0.1",
    author="Rob deCarvalho",
    author_email="unlisted",
    description=("Stream Procesing"),
    license="BSD",
    keywords="python stream processing apache storm concurrent",
    url="https://github.com/robdmc/consecution",
    packages=find_packages(),
    #package_data={'value': ['glob']},
    # include_package_data=True,
    long_description=LONG_DESCRIPTION,
    classifiers=[
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Topic :: Distributed Computing',
    ],
    install_requires = [
        'django>=1.7',
    ],
    tests_require=[
        'django-nose>=1.4',
        'mock==1.0.1',
        'coverage>=3.7.1',
    ],
    #entry_points={
    #    'console_scripts': [
    #    ],
    #}
)
