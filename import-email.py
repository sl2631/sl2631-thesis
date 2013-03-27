#!/usr/bin/env python2.7

from __future__ import print_function

import datetime
import calendar
import imaplib
import email
import email.header
import sys
import pickle
import re
import os
import os.path

from pprint import pprint


server = 'imap.gmail.com'
username, password = sys.argv[1:3]
labels_to_fetch = sys.argv[3:] # optional

root_dir = username

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


def decode_string(string, charset):
  if charset is None:
    charset = 'utf-8'
  return string.decode(encoding=charset, errors='replace')


def decode_header(h):
  'convert an encoded email header into a unicode string.'
  decoded_list = email.header.decode_header(h)
  #print('decode_list:', decoded_list)
  decoded_first = decoded_list[0]
  string, charset = decoded_first
  return decode_string(string, charset)
  # note: reportlab probably expects the string to be converted into utf-8
  #converted = s.encode('utf-8')


def dates_for_month(year, month):
  dates = []
  for i in range(calendar.monthrange(year, month)[1]):
    date = datetime.date(year, month, i + 1)
    dates.append(date)
  return dates


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


def write_pickle(obj, path):
  with open(path, 'w') as f:
    pickle.dump(obj, f)


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
  for index, uid in enumerate(uid_list):
    if limit >= 0 and index >= limit:
      break
    print("fetching:", uid)
    # uid is the name of the function for sending IMAP commands using UIDs instead of numerical indices
    # uid is also the name of our local variable
    status, data = account.uid('fetch', uid, "(RFC822)")
    assert status == 'OK'
    # data is a list of tuples
    email_tuple = data[0]
    if not email_tuple:
      print('empty email_tuple:', email_tuple)
      continue
    # each tuple has format: ('0 (UID 0 RFC822 {11287}', contents, ')')
    message = email.message_from_string(email_tuple[1])
    parts = []
    for part in message.walk():
      # each part is a either non-multipart, or a multipart message that contains further parts.
      # for now only pay attention to the text parts (leaves of a the multipart tree).
      if part.get_content_type() == 'text/plain':
        parts.append(decode_string(part.get_payload(), part.get_charset()))

    headers = { k : decode_header(message[k]) for k in message.keys() }
    message_dict = {
      'uid'   : uid,
      'label' : label,
      'parts' : parts,
      # use empty strings as defaults 
      'from'  : headers.get('From', ''),
      'to'    : headers.get('To', ''),
      'date'  : headers.get('Date', ''),
      'subject' : headers.get('Subject', ''),
    }

    # used to write a pickle for each message; not useful at this point
    if False:
      out_path = os.path.join(dst_dir, '{}.pickle'.format(uid))
      write_pickle(message_dict, out_path)
    messages.append(message_dict)

  out_path = os.path.join(root_dir, label_safe + '.pickle')
  write_pickle(messages, out_path)


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
