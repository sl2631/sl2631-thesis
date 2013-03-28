#!/usr/bin/env python2.7

from __future__ import print_function
from __future__ import unicode_literals

import imaplib
import sys
import re
import os
import os.path
import thesis_util
from pprint import pprint


server = 'imap.gmail.com'
username, password, start_uid_str = sys.argv[1:4]
start_uid = int(start_uid_str)
labels_to_fetch = sys.argv[4:] # optional

root_dir = username + '-data'

if not os.path.isdir(root_dir):
  print('making dir:', root_dir)
  os.makedirs(root_dir)


# comment out the labels that you do not want excluded
excluded_labels = {
  '[Gmail]',
  '[Gmail]/All Mail',
  '[Gmail]/Drafts',
  #'[Gmail]/Important',
  #'[Gmail]/Sent Mail',
  '[Gmail]/Spam',
  '[Gmail]/Starred',
  '[Gmail]/Trash',
}

# connect to the email server
account = imaplib.IMAP4_SSL(server)
account.login(username, password)


def select_label(label):
  quoted = '"{}"'.format(label)
  print('\nselect:', quoted)
  status, label_count = account.select(quoted)
  assert status == 'OK'
  print('label_count:', status, label_count)


def search_by_send_date(date):
  '''
  search for messages by send date; return a list of ids.
  NOTE: this is untested code from a previous example; note it also searches for a specific hard-coded sender.
  '''
  imap_date = date.strftime("%d-%b-%Y")
  status, data = account.uid('search', None, '(SENTON {date} HEADER TO itp-students@lists.nyu.edu)'.format(date=imap_date))
  assert status == 'OK'
  ids = data[0] # data is a list.
  id_list = ids.split() # ids is a space separated string
  return id_list


def fetch_label(label):
  label_safe = re.sub('[^0-9a-zA-Z_]', '_', label)

  select_label(label)
  status, data = account.uid('search', None, 'ALL')
  assert status == 'OK'
  uids = data[0] # data is a list of space-separated uid list strings.
  uid_list = [int(s) for s in uids.split()]
  print('{} items'.format(len(uid_list)))

  limit = -1
  messages = []
  last_uid = 'none'
  try:
    for index, uid in enumerate(uid_list):
      if uid < start_uid:
        continue
      if limit >= 0 and index >= limit: # debug limit
        break
      print("fetching:", uid, end='\r')
      sys.stdout.flush()
      # uid is the name of the function for sending IMAP commands using UIDs instead of numerical indices
      # uid is also the name of our local variable
      status, data = account.uid('fetch', uid, "(RFC822)")
      assert status == 'OK'
      messages.append(data)
      last_uid = uid
  except BaseException as e:
    print('\nfailed at uid:', uid, '\n', e)
  else:
    print()
  out_path = os.path.join(root_dir, '{}-{}-{}.pickle'.format(label_safe, start_uid, last_uid))
  thesis_util.write_pickle(messages, out_path)


def fetch_all_labels():
  # format is (attributes, root? (i.e. '/'), name)
  contents_re = re.compile(r'\(([^)]+)\) "([^"]+)" "([^"]+)"')

  status, raw_list = account.list()
  assert status == 'OK'
  all_labels = []
  for s in raw_list:
    m = contents_re.match(s)
    assert m
    g = m.groups()
    all_labels.append(g[2].decode('utf-8')) # for now we are only interested in the name
  print('\nall labels:')
  pprint(all_labels)

  labels = [l for l in all_labels if (labels_to_fetch or not l in excluded_labels)]
  print('\nlabels:')
  pprint(labels)

  # python docs example suggests we can select everything as follows:
  #account.select()
  # for now, iterate over each label
  for label in labels:
    if labels_to_fetch and label not in labels_to_fetch:
      continue
    fetch_label(label)


labels_dict = fetch_all_labels()
