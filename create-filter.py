#!/usr/bin/env python2.7

from __future__ import print_function

import sys
import pickle
import re

from pprint import pprint

filter_path = 'picklelaffont.filter'
in_paths = sys.argv[1:]

filter_dict = {}
with open(filter_path) as f:
  for raw_line in f:
    line = raw_line.strip()
    choice, space, address = line.partition(' ')
    if not space or choice not in '+-': # partition failed or bad choice symbol
      print('bad filter line:', repr(line))
      sys.exit(1)
    filter_dict[address] = (choice == '+')


email_re = re.compile('<(.+)>')
ff = open(filter_path, 'a')

def handle_message(message):
  # keys: ['from', 'uid', 'label', 'to', 'parts', 'date', 'subject']
  sender = unicode(message['from']).encode('ascii', 'replace') # must make addresses ascii-clean before writing to filter file
  if not sender: # some from headers were missing
    print('missing sender: uid:', message['uid'])
    return
  m = email_re.search(sender)
  if m:
    address = m.group(1)
  else:
    # just assume that the whole sender string is the address
    # TODO: we could use another regex to validate this address but it's a pain
    address = sender
  if address in filter_dict:
    return # we have already created a filter rule for this address

  # present the user with a choice
  choice = None
  while choice not in {'y', 'n'}:
    if choice:
      print('invalid choice:', choice)
    prompt = u'\nfrom: {from}\nto: {to}\nsubject: {subject}\n(y/n)> '.format(**message)
    choice = raw_input(prompt.encode('utf-8')).strip()
  allowed = (choice == 'y')
  filter_dict[address] = allowed
  filter_string = '{} {}'.format(('+' if allowed else '-'), address)
  print(filter_string)
  ff.write(filter_string)
  ff.write('\n')

try:
  for in_path in in_paths:
    with open(in_path) as f:
      messages = pickle.load(f)
      print(in_path, 'count:', len(messages))
      for message in messages:
        try:
          handle_message(message)
        except:
          print("failed with message:")
          pprint(message)
          raise

except:
  ff.close() # want to make sure we flush all data before exiting
  raise
