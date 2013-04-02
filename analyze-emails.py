#!/usr/bin/env python2.7

from __future__ import print_function
from __future__ import unicode_literals

import collections
import sys
import re
import nltk
import nltk.stem
import thesis_util

from thesis_util import *
from pprint import pprint


modes = { 'scan', 'dump' }

word_re = re.compile("^[-'\w]+$")

# regexes remove uninteresting parts of messages
# two basic categories; those that scan across lines (DOTALL) and those that matcha  single line.
scrub_regexes = \
[re.compile(p, flags=re.DOTALL | re.MULTILINE) for p in [
# patterns that scan across lines need dot to include \n
  r'^On [^\n]+ at [^\n]+, [^\n]+ ?wrote:.*',
  r'^----- Original Message -----.*',
  r'^------Original Message------.*',
  r'^Sent from my .+',
  r'^Admissions, Special Events, Alumni Coordinator.*',
]] + \
[re.compile(p, flags=re.MULTILINE) for p in [
# patterns that scan per line need ^ to match each start of line
  r'^[> ]+.*\n',
  r'^You are currently subscribed to .*\n?',
  r'^To unsubscribe send a blank email to .*\n?',
]]


# NLP tools

_lemmatizer = nltk.stem.WordNetLemmatizer()
def lemmatize(word):
  '''
  returns word unchanged if not found. does not appear to handle the following:
  - gerunds, e.g. 'running'
  - irregular past tense, e.g. 'ran'
  '''
  return _lemmatizer.lemmatize(word)


_lancaster_stemmer = nltk.stem.lancaster.LancasterStemmer()
def stem_heavy(word):
  return _lancaster_stemmer.stem(word)


# command line args

def error(msg):
  print('error:', msg)
  print('specify mode as first argument; options are:', modes)
  sys.exit(1)

try:
  mode = unicode(sys.argv[1])
  if mode not in modes:
    error('invalid mode')
except IndexError:
  error('no mode specified')
is_mode_dump = (mode == 'dump')
is_mode_scan = (mode == 'scan')

in_paths = sys.argv[2:]
if not in_paths:
  in_paths = ['slaffont-emails/all_mail.pickle']


# stats
message_count = 0
skip_count = 0

if is_mode_scan:

  stats = collections.defaultdict(collections.Counter)
  def count(group, key):
    stats[group][key] += 1

  words = stats['words']
  non_words = stats['non-words']



def scrub(text):
  for r in scrub_regexes:
    text = r.sub('', text)
  return text


def scan(text):
  sentences = thesis_util.sent_word_tokenize(text) # nested sentence->words
  for sentence in sentences:
    for t in sentence:
      m =  word_re.match(t)
      if m:
        words[t.lower()] += 1
      else:
        non_words[t.lower()] += 1


address_filter_neg = thesis_util.load_filter_neg(address_filter_path)

for in_path in in_paths:
  messages = thesis_util.read_pickle(in_path)
  print('\n', in_path, sep='')
  for index, message in enumerate(messages):
    #if index > 1000: break
    addr_from = message['from']
    addr_to = message['to']
    if addr_from in address_filter_neg or addr_to in address_filter_neg:
      skip_count += 1
      continue
    message_count +=1
    # dump
    subject = message['subject']
    text = scrub(message['text'])
    if is_mode_dump:
      print('=' * 96)
      print(addr_from, '-', addr_to, '-', subject)
      print('-' * 96)
      print(text)
    else:
      progress(index)
    if is_mode_scan:
      scan(subject)
      scan(text)

if is_mode_scan:
  print()
  for name, counter in sorted(stats.items()):
    print('\n', name, '; count = ', len(counter), sep='')
    for k, count in sorted(counter.items(), key=lambda p: p[1]):
      print('{:>5}: {}'.format(count, k))


print('messages used:', message_count)
print('messages skipped:', skip_count)
