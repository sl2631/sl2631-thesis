#!/usr/bin/env python2.7

from __future__ import print_function
from __future__ import unicode_literals

import sys
import re
import os.path
import email
import email.header
import thesis_util
from pprint import pprint


in_paths = sys.argv[1:]


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


def process_message_data(data):
  # data is a list of tuples
  email_tuple = data[0]
  if not email_tuple:
    print('empty email_tuple:', email_tuple)
    return None
  # each tuple has format: ('0 (UID 0 RFC822 {11287}', contents, ')')
  message = email.message_from_string(email_tuple[1])
  parts = []
  for part in message.walk():
    # each part is a either non-multipart, or a multipart message that contains further parts.
    # for now only pay attention to the text parts (leaves of a the multipart tree).
    if part.get_content_type() == 'text/plain':
      payload = part.get_payload(decode=True) # take care of quoted-printable or base64 encodings
      #charset = part.get_charset() # this seems to always be None
      content_charset = part.get_content_charset()
      parts.append(decode_string(payload, content_charset))

  headers = { k : decode_header(message[k]) for k in message.keys() }
  return {  
    'text' : '\n'.join(parts),
    # use empty strings as defaults to ease error handling
    'from'  : headers.get('From', ''),
    'to'    : headers.get('To', ''),
    'date'  : headers.get('Date', ''),
    'subject' : headers.get('Subject', ''),
  }


for in_path in in_paths:
  in_dir, in_name = os.path.split(in_path)
  end = '-data'
  assert in_dir.endswith(end)
  out_dir = in_dir[:-len(end)]
  out_path = os.path.join(out_dir, in_name)
  if not os.path.isdir(out_dir):
    os.makedirs(out_dir)
  in_messages = thesis_util.read_pickle(in_path)
  out_messages = []
  for index, data in enumerate(in_messages):
    out_message = process_message_data(data)
    if False:
      pprint(out_message)
      print('{}: {from} - {to} - {subject}\n{text}'.format(index, **out_message))
    out_messages.append(out_message)
  thesis_util.write_pickle(out_messages, out_path)
