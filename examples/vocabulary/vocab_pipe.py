#! /usr/bin/env python

import sys
import re
sys.path.append('../..')
from consecution import Node, Pipeline
from collections import Counter
from math import log, exp


class FileReader(Node):
    def begin(self):
        self.rexp_allowed_chars = re.compile(r"""([^a-z \.\?!:;,\-])""")
        self.rexp_punctuation = re.compile(r"""([\.\?!:;,\-"'])""")

    def process(self, file_name):
        author = file_name.split('__')[0]
        with open(file_name.strip()) as file_buffer:
            text = file_buffer.read().decode('utf8').lower()
            for line in (l.strip() for l in text.split('\n') if l.strip()):
                line = re.sub(self.rexp_allowed_chars, '', line)
                line = re.sub(self.rexp_punctuation, ' ', line)
                for word in line.split():
                    self.push((author, word))

class WordCounter(Node):
    def begin(self):
        self.counts_for_author = {}

    def process(self, tup):
        author, word = tup
        if not author in self.counts_for_author:
            self.counts_for_author[author] = Counter()
        self.counts_for_author[author].update({word: 1})

    def end(self):
        for author, counter in self.counts_for_author.items():
            counts = [c for c in counter.values()]
            self.push((author, counts))

class TotalCountCalc(Node):
    def begin(self):
        self.out_list = []

    def process(self, tup):
        author, counts = tup
        self.out_list.append((author, len(counts)))

    def end(self):
        print
        print '-' * 80
        print 'Sorted by total number of unique words'
        for tup in sorted(self.out_list, key=lambda t: t[1]):
            print '{0: <30s} {1}'.format(*tup)

class DiversityCalc(Node):
    def begin(self):
        self.out_list = []

    def process(self, tup):
        author, counts = tup
        total = float(sum(counts))
        probs = (c / total for c in counts)
        entropy = sum((-p * log(p) for p in probs))
        diversity = exp(entropy)
        self.out_list.append((author, int(round(diversity))))

    def end(self):
        print
        print '-' * 80
        print 'Sorted by total word diversity'
        for tup in sorted(self.out_list, key=lambda t: t[1]):
            print '{0: <30s} {1}'.format(*tup)

##class EntropyCalc(Node):
##class DiversityCalc(Node):
#class DiversityCalc(Node):
#    def begin(self):
#        self.diversity_list = []
#
#    def process(self, tup):
#        author, counts = tup
#        total = float(sum(counts))
#        probs = (c / total for c in counts)
#        entropy = sum((-p * log(p) for p in probs))
#        diversity = exp(entropy)
#        total_words = len(counts)
#
#        self.diversity_list.append((author, diversity, total_words))
#
#    def end(self):

#class WordSortedPrinter(Node):
#    def process(self, diversity_list):
#
#class DiversitySortedPrinter(Node):
#    def process(self, diversity_list):

#class Printer(Node):
#    def process(self, item):
#        print item


pipeline = Pipeline(
    FileReader('file_reader') | WordCounter('word_counter') |
    [
        TotalCountCalc('total_count'),
        DiversityCalc('diversity_calc')
    ]
    #Printer('printer')
)

pipeline.consume(sys.stdin.readlines())


#print
#print pipeline
#sys.exit()
#
#
#text = sys.stdin.read()
#text = text.decode('utf8')
#text = text.lower()
#
#rexp_allowed_chars = re.compile(r"""([^a-z \.\?!:;,\-])""")
#rexp_punctuation = re.compile(r"""([\.\?!:;,\-"'])""")
#
#
#for line in text.split('\n'):
#    line = line.strip()
#    line = re.sub(rexp_allowed_chars, '', line)
#    line = re.sub(rexp_punctuation, ' ', line)
#    print line
#

