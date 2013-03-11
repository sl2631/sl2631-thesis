#!/usr/bin/env python2.7

from __future__ import print_function

import datetime
import calendar
import collections
import sys
import pickle
import re
import nltk

from pprint import pprint

in_paths = sys.argv[1:]

word_counter = collections.Counter()

for in_path in in_paths:
  with open(in_path) as f:
    messages = pickle.load(f)
    print(in_path, 'count:', len(messages))
    for index, message in enumerate(messages):
      #if index > 2: break
      # keys: ['from', 'uid', 'label', 'to', 'parts', 'date', 'subject']
      for raw_part in message['parts']:
        part = raw_part.replace('=\r\n', '')
        lowered = part.lower()
        tokens = nltk.word_tokenize(lowered)
        if False:
          print(repr(part))
          print(part)
          print(tokens)
          print('\n\n')
        word_counter.update(tokens)

pprint(sorted(word_counter.items(), key=lambda p: p[1]))
