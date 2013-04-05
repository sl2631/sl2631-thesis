#!/usr/bin/env python2.7

from __future__ import print_function
from __future__ import unicode_literals

import sys
import pickle
from thesis_util import *
from pprint import pprint


in_paths = sys.argv[1:]
if not in_paths:
  in_paths = ['slaffont-emails/all_mail.pickle']

try:
  address_filter_dict = load_filter(address_filter_path)
except IOError:
  print('no existing filter:', address_filter_path)
  address_filter_dict = {}

ff = open(address_filter_path, 'a')

def handle_message(message):
  sender = message['from'].lower()
  if not sender: # from header may be missing
    print('missing sender: uid:', message['uid'])
    return
  address = email_or_sender(sender)
  if address in address_filter_dict:
    return # we have already created a filter rule for this address

  print('\nfrom: {from}\nto: {to}\nsubject: {subject}'.format(**message))
  # present the user with a choice
  choice = None
  while choice not in {'y', 'n'}:
    if choice:
      print('invalid choice')
    prompt = 'address: {}\n(y/n)> '.format(address)
    choice = raw_input(prompt).strip()
  allowed = (choice == 'y')
  address_filter_dict[address] = allowed
  filter_string = '{} {}\n'.format(('+' if allowed else '-'), address)
  print(filter_string, end='')
  ff.write(filter_string.encode('utf-8'))
  ff.flush()

for in_path in in_paths:
  messages = read_pickle(in_path)
  print(in_path, 'count:', len(messages))
  for message in messages:
    try:
      handle_message(message)
    except Exception:
      print("failed with message:")
      pprint(message)
      raise
    except KeyboardInterrupt:
      print('\nexiting.')
      sys.exit(0)
