#!/usr/bin/env python2.7

from __future__ import print_function
from __future__ import unicode_literals

import sys
import re
import os.path
import email
import email.header
from thesis_util import *


out_path = sys.argv[1]
in_paths = sys.argv[2:]


useful_header_keys = [
  'cc',
  'date',
  'from',
  'subject',
  'to',
]

charset_encoding = {
  None : 'utf-8',
  'windows-1252http-equivcontent-type' : 'windows-1252',
}

def decode_string(string, charset):
  enc = charset_encoding.get(charset, charset)
  return string.decode(encoding=enc, errors='replace')


def decode_header(h):
  'convert an encoded email header into a unicode string.'
  decoded_list = email.header.decode_header(h)
  #print('decode_list:', decoded_list)
  decoded_first = decoded_list[0]
  string, charset = decoded_first
  return decode_string(string, charset)


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

  headers = { unicode(k.lower()) : decode_header(message[k]) for k in message.keys() if k.lower() in useful_header_keys }
  msg = { 'text' : '\n'.join(parts) }
  for k in useful_header_keys:
    msg[k] = headers.get(k, '')
  return msg


messages = []
for in_path in in_paths:
  print('reading:', in_path)
  in_messages = read_pickle(in_path)
  for index, data in enumerate(in_messages):
    progress(index)
    m = process_message_data(data)
    if False:
      pprint(m)
    messages.append(m)
  print()

print('writing:', out_path)
write_pickle(messages, out_path)
