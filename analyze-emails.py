#!/usr/bin/env python2.7

from __future__ import print_function
from __future__ import unicode_literals

import collections
import sys
import re
import nltk
import thesis_util
from thesis_util import sender_filter_path
from pprint import pprint

in_paths = sys.argv[1:]

sender_filter_neg = thesis_util.load_filter_neg(sender_filter_path)
word_counter = collections.Counter()

scrub_regexes = \
[re.compile(p, flags=re.DOTALL | re.MULTILINE) for p in [
# patterns that scan across lines need dot to include \n
  r'^On [^\n]+ at [^\n]+, [^\n]+ wrote:.*',
  r'^----- Original Message -----.*',
  r'^Sent from my .+',
]] + \
[re.compile(p, flags=re.MULTILINE) for p in [
# patterns that scan per line need ^ to match each start of line
  r'^[> ]+.*\n',
  r'^You are currently subscribed to .*\n?',
  r'^To unsubscribe send a blank email to .*\n?',
]]


def scrub(part):
  for r in scrub_regexes:
    part = r.sub('', part)
  return part


for in_path in in_paths:
  messages = thesis_util.read_pickle(in_path)
  print(in_path, 'count:', len(messages))
  for index, message in enumerate(messages):
    sender = message['from']
    if sender in sender_filter_neg:
      continue
    subject = message['subject']
    print('*' * 64, '\n', sender, '-', subject)
    text = scrub(message['text'])
    print('-' * 64, '\n', text, sep='')
    tokens = thesis_util.sent_word_tokenize(text) # nested sentence->words
    for sentence in tokens:
      word_counter.update(sentence)
         
pprint(sorted(word_counter.items(), key=lambda p: p[1]))
