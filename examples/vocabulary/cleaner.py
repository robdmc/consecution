#! /usr/bin/env python
"""
This script should get incorporated into a node.  It lower cases all words
and removes non-word characters
"""

import re
import sys

text = sys.stdin.read()
text = text.decode('utf8')
text = text.lower()

rexp_allowed_chars = re.compile(r"""([^a-z \.\?!:;,\-])""")
rexp_punctuation = re.compile(r"""([\.\?!:;,\-"'])""")


for line in text.split('\n'):
    line = line.strip()
    line = re.sub(rexp_allowed_chars, '', line)
    line = re.sub(rexp_punctuation, ' ', line)
    print line
