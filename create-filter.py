#!/usr/bin/env python3

import sys
import pickle
from thesis_util import *
from pprint import pprint


try:
  address_filter_dict = load_filter(address_filter_path)
except IOError:
  print('no existing filter:', address_filter_path)
  address_filter_dict = {}

ff = open(address_filter_path, 'a')


def handle_message(message):
  handle_address(message['from'])
  handle_address(message['to'])


def handle_address(address):
  address = email_or_sender(address.lower())
  # just skip addresses with no sender or recipient
  # skip if we have already created a filter rule for this address
  if not address or address in address_filter_dict:
    return 
  print('\nfrom: {from}\nto: {to}\nsubject: {subject}'.format(**message))

  # present the user with a choice
  choice = None
  while choice not in {'y', 'n'}:
    if choice:
      print('invalid choice')
    prompt = 'address: {}\n(y/n)> '.format(address)
    choice = input(prompt)
  allowed = (choice == 'y')
  address_filter_dict[address] = allowed
  filter_string = '{} {}\n'.format(('+' if allowed else '-'), address)
  print(filter_string, end='')
  ff.write(filter_string)
  ff.flush()


message_dict = read_pickle(in_path)
print(in_path, 'count:', len(message_dict))
for uid, message in message_dict.items():
  try:
    handle_message(message)
  except Exception:
    print("failed with message:")
    pprint(message)
    raise
  except KeyboardInterrupt:
    print('\nexiting.')
    sys.exit(0)
