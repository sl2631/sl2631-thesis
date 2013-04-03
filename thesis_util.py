'''
thesis utility functions common across scripts.
'''

from __future__ import print_function
from __future__ import unicode_literals

import calendar
import codecs
import datetime
import sys
import pickle
import email
import email.header

import nltk.tokenize
from pprint import pprint

# wrap sys.stdout with a utf-8 stream writer
# this fixes ascii encoding errors when redirecting output to a file.
sys.stdout = codecs.getwriter('utf-8')(sys.stdout) 


address_filter_path = 'slaffont-address-filter.txt'


def errL(*items):
  print(*items, file=sys.stderr)

def progress(i):
  if i % 1000 == 0:
    print('\r{}k'.format(i // 1000), end='', file=sys.stderr)
    sys.stderr.flush()


def plabel(label, obj):
  print(label)
  pprint(obj)


def read_pickle(path):
  with open(path) as f:
    return pickle.load(f)


def write_pickle(obj, path):
  with open(path, 'w') as f:
    pickle.dump(obj, f)


def read_word_list(path):
  with open(path) as f:
    return { line.decode('utf-8').strip() for line in f }


def dates_for_month(year, month):
  'from old example; currently unused.'
  return [datetime.date(year, month, i + 1) for i in range(calendar.monthrange(year, month)[1])]


def load_filter(filter_path):
  'filter dictionary representing both whitelisted and blacklisted items (+/-).'
  filter_dict = {}
  with open(filter_path) as f:
    for raw_line in f:
      line = raw_line.decode('utf-8').strip()
      choice, space, address = line.partition(' ')
      if not space or choice not in '+-': # partition failed or bad choice symbol
        errL('bad filter line:', repr(line))
        sys.exit(1)
      filter_dict[address] = (choice == '+')
  return filter_dict


def load_filter_pos(filter_path):
  'set of whitelisted filter items.'
  filter_dict = load_filter(filter_path)
  return set(k for k, v in filter_dict.items() if v)


def load_filter_neg(filter_path):
  'set of blacklisted filter items.'
  filter_dict = load_filter(filter_path)
  return set(k for k, v in filter_dict.items() if not v)


def sent_word_tokenize(string):
  return [nltk.tokenize.word_tokenize(sentence) for sentence in nltk.tokenize.sent_tokenize(string)]


