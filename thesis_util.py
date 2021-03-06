'''
thesis utility functions common across scripts.
'''

import calendar
import codecs
import datetime
import sys
import pickle
import email
import email.header
import re

from pprint import pprint


address_filter_path = 'slaffont-address-filter.txt'
in_path = 'slaffont-data/all.pickle'


# approximate email regex;
# omits the single-quote as a valid char, as it is showing up in strange places.
# ignores the following special characters, which may only be used within quotations.
# space, "(),:;<>@[\]
# comments (leading or trailing parentheticals) are also ignored.
# International characters above U+007F are allowed; we allow up to the max code point.
# use ur prefix to only escape \u and \U.
email_re = re.compile(r"[a-zA-Z0-9!#$%&*+-/=?^_`{|}~.\u007f-\U0010FFFF]+@[a-zA-Z0-9.-]+")


def email_or_sender(sender):
  s = sender.lower() # email is technically case sensitive but we do this to increase filter hits
  m = email_re.search(s)
  return m.group(0) if m else s


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
  with open(path, 'rb') as f:
    return pickle.load(f)


def write_pickle(obj, path):
  with open(path, 'wb') as f:
    pickle.dump(obj, f)


def read_word_list(path):
  with open(path) as f:
    return { line.strip() for line in f }


def dates_for_month(year, month):
  'from old example; currently unused.'
  return [datetime.date(year, month, i + 1) for i in range(calendar.monthrange(year, month)[1])]


def load_filter(filter_path):
  'filter dictionary representing both whitelisted and blacklisted items (+/-).'
  filter_dict = {}
  with open(filter_path) as f:
    for raw_line in f:
      line = raw_line.strip()
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

