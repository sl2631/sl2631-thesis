#!/usr/bin/env python3

import collections
import sys
import re
import itertools
import thesis_util

from thesis_util import *
from pprint import pprint

list_limit = 10

modes = { 'count', 'dump', 'sentence' }


# regexes remove uninteresting parts of messages
# two basic categories; those that scan across lines (DOTALL) and those that match a single line.
scrub_regexes = \
[re.compile(p, flags=re.DOTALL | re.MULTILINE) for p in [
# patterns that scan across lines need dot to include \n
  r'^On [^\n]+ (at )?[^\n]+, [^\n]+ ?wrote:.*',
  r'^-+ *Original Message *-+.*',
  r'^Sent from my .+',
  r'^Admissions, Special Events, Alumni Coordinator.*',
  r'^________________________________.+This message is solely for the use of the intended recipient.+',
]] + \
[re.compile(p, flags=re.MULTILINE) for p in [
# patterns that scan per line need ^ to match each start of line
  r'^[> ]+.*\n',
  r'^You are currently subscribed to .*\n?',
  r'^To unsubscribe send a blank email to .*\n?',
]]


# command line args

def error(msg):
  errL('error:', msg)
  errL('usage: analyze-emails.py MODE SENDER PHRASE')
  errL('available modes:', *modes)
  sys.exit(1)

try:
  mode = sys.argv[1]
  if mode not in modes:
    error('invalid mode')
except IndexError:
  error('no mode specified')

is_mode_count     = (mode == 'count')
is_mode_dump      = (mode == 'dump')
is_mode_sentence  = (mode == 'sentence')

args = sys.argv[2:]
target_sender = args[0]
target_phrase = args[1]

if is_mode_count:
  stats = collections.defaultdict(collections.Counter)
  def count(group, key):
    stats[group][key] += 1
  word_counter = stats['words']
else:
  def count(group, key):
    pass

if is_mode_sentence:
  if not target_phrase:
    error('sentence mode requires a non-empty target phrase')

def scrub(text):
  for r in scrub_regexes:
    text = r.sub('', text)
  return text


# word_re captures splitting words; hyphen and apostrophe allowed only as internal characters.
word_re = re.compile(r"(\w(?:[-'\w]*\w)?)")
space_re = re.compile(r'\s+')

def count_text(text, groups):
  tokens = word_re.split(text)
  #non_words = tokens[0::2]
  words = [t.lower() for t in tokens[1::2]]
  #print('tokens:', tokens)
  #print('words:', words)
  #print('non-words:', non_words)
  #print()
  #for t in non_words: non_word_char_counter.update(t) # count individual chars
  # always count the words in the main counter
  word_counter.update(words)
  # for each specific group, also count these words towards that group
  for g in groups:
    stats[g].update(words)


address_filter_neg = thesis_util.load_filter_neg(address_filter_path)


def clean_text(text):
  tokens = word_re.split(text)
  #print('pre: ', text, tokens, file=sys.stderr)
  for i, t in enumerate(tokens):
    if i % 2: continue # odd elements are words, which we leave alone
    s = space_re.sub(' ', t) # replace arbitrary spacing with a single space char
    tokens[i] = s
  cleaned = ''.join(tokens)
  #print('post:', cleaned, tokens, file=sys.stderr)
  return cleaned


def find_target_phrase(text, start=0):
  return text.find(target_phrase, start)


def find_dot_rev(string, index):
  for i in range(index, -1, -1): # step backwards
    if string[i] == '.':
      return i
  return -1


def extract_target_sentences(text):
  lc_text = text.lower()
  start = 0
  while start < len(text):
    phrase_index = find_target_phrase(lc_text, start)
    if phrase_index < 0:
      return
    start = find_dot_rev(text, phrase_index - 1) + 1 # sentence begins after the preceding dot
    end = text.find('.', phrase_index + len(target_phrase))
    if end < 0:
      end = len(text)
    yield text[start:end + 1].strip() # sentence includes terminating dot
    start = end


def print_message(addr_from, addr_to, date, subject, text):
  print('\nFROM:    ', addr_from,
        '\nTO:      ', addr_to,
        '\nDATE:    ', date,
        '\nSUBJECT: ', subject)
  print()
  print(text)
  print()


def print_sentences(addr_from, addr_to, date, subject, text):
  once = False
  sentences = list(extract_target_sentences(subject)) + list(extract_target_sentences(text))
  if not sentences:
    return
  print_message(addr_from, addr_to, date, subject, '\n'.join(sentences))


# stats
message_count = 0
skip_count = 0

def handle_message(index, uid, message):
  global message_count, skip_count
  addr_from = email_or_sender(message['from'])
  addr_to = email_or_sender(message['to'])
  if addr_from in address_filter_neg or addr_to in address_filter_neg or (target_sender and addr_from != target_sender):
    skip_count += 1
    count('skip-from', addr_from)
    count('skip-to', addr_to)
    return
  message_count +=1
  count('from', addr_from)
  count('to', addr_to)

  date = message['date']
  subject = message['subject']
  text = scrub(message['text'])

  if is_mode_count:
    progress(index)
    sender_group = 'words from: ' + addr_from
    groups = [sender_group]
    count_text(subject, groups)
    count_text(text, groups)

  elif is_mode_dump:
    if not target_phrase or find_target_phrase(clean_text(subject)) >= 0 or find_target_phrase(clean_text(text)) >= 0:
      print_message(addr_from, addr_to, date, subject, text)

  elif is_mode_sentence:
    print_sentences(addr_from, addr_to, date, clean_text(subject), clean_text(text))



message_dict = thesis_util.read_pickle(in_path)
print(in_path)
for index, (uid, m) in enumerate(sorted(message_dict.items())):
  try:
    handle_message(index, uid, m)
  except:
    errL('error at uid:', uid)
    raise

if is_mode_count:
  errL() # for progress line
  for group, counter in sorted(stats.items()):
    try:
      total = sum(counter.values())
      print('\n', group, ': distinct = ', len(counter), '; total = ', total, sep='')
      items = sorted((v, k) for k, v in counter.items())
      for count, k in items[-list_limit-1:]:
        try:
          fraction = count / total
          print('  {:.5f} {:>5}: {}'.format(fraction, count, k))
        except:
          errL('error for key:', k)
          raise
    except:
      errL('error for group:', group)
      raise

  print('\nword ratios')
  words_total = sum(word_counter.values())

  for group, counter in stats.items():
    if group.startswith('words from: '):
      from_total = sum(counter.values())
      if from_total == 0:
        continue
      total_ratio = words_total / from_total
      ratios = sorted((total_ratio * v / word_counter[k], k) for k, v in counter.items())
      print('\nratios of ' + group)
      print(*('  {:6.1f}: {}'.format(*r) for r in ratios[-list_limit:]), sep='\n')

  if False:
    print('\nall non-unique words:')
    word_items = sorted(word_counter.items(), key=lambda p: (-p[1], p[0]))
    print(*(p[0] for p in word_items if p[1] > 1))

print()
print('messages used:', message_count)
print('messages skipped:', skip_count)
