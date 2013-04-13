#!/usr/bin/env python3

import collections
import sys
import re
import itertools
import thesis_util
import time as _time

from thesis_util import *
from pprint import pprint

list_limit = 10


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

modes = { 'count', 'dump', 'sentence' }


def msg_key_from(msg_pair):
  return email_or_sender(msg_pair[1]['from'])

def msg_key_to(msg_pair):
  return email_or_sender(msg_pair[1]['to'])

def msg_key_date(msg_pair):
  try:
    date = msg_pair[1]['date']
    return _time.mktime(_time.strptime(date, '%a, %d %b %Y %H:%M:%S +0000'))
  except (KeyError, ValueError):
    return 0

def msg_key_subject(msg_pair):
  return msg_pair[1]['subject'].lower().strip()

sort_keys = {
  'none'    : None,
  'from'    : msg_key_from,
  'to'      : msg_key_to,
  'date'    : msg_key_date,
  'subject' : msg_key_subject,
}


def error(msg):
  errL('error:', msg)
  errL('usage: analyze-emails.py MODE SORT SENDER PHRASE')
  errL('available modes:', *modes)
  errL('available sorts:', *sort_keys.keys())
  sys.exit(1)

args = sys.argv[1:]

try:
  mode = args[0]
  if mode not in modes:
    error('invalid mode')
except IndexError:
  error('no mode specified')

is_mode_count     = (mode == 'count')
is_mode_dump      = (mode == 'dump')
is_mode_sentence  = (mode == 'sentence')

target_sort = args[1]
target_sender = args[2]
target_phrase = args[3]

if is_mode_count:
  stats = collections.defaultdict(collections.Counter)
  def count(group, key, inc=1):
    stats[group][key] += inc
  word_counter = stats['words']
  sort_key = None
else:
  def count(group, key, inc=1):
    pass
  try:
    sort_key = sort_keys[target_sort]
  except KeyError:
    error('invalid sort')

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


def contains_phrase(text):
  return find_target_phrase(clean_text(text.lower())) >= 0


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


def count_target_sentences(text):
  return len(list(extract_target_sentences(text)))


def print_message(addr_from, addr_to, date, subject, text):
  print('\nFROM:    ', addr_from,
        '\nTO:      ', addr_to,
        '\nDATE:    ', date,
        '\nSUBJECT: ', subject)
  print()
  print(text.strip())
  print('\n' + '-' * 64)


def print_sentences(addr_from, addr_to, date, subject, text):
  once = False
  sentences = list(extract_target_sentences(subject)) + list(extract_target_sentences(text))
  if not sentences:
    return 0
  print_message(addr_from, addr_to, date, subject, '\n'.join(sentences))
  return len(sentences)

# stats
message_count = 0
skip_count = 0
hit_count = 0

def handle_message(index, uid, message):
  global message_count, skip_count, hit_count
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
    phrase_count = count_target_sentences(subject) + count_target_sentences(text)
    count('phrase from', addr_from, inc=phrase_count)
    count('phrase to', addr_to, inc=phrase_count)


  elif is_mode_dump:
    if not target_phrase or contains_phrase(subject) or contains_phrase(text):
      print_message(addr_from, addr_to, date, subject, text)
      hit_count += 1

  elif is_mode_sentence:
    hit_count += print_sentences(addr_from, addr_to, date, clean_text(subject), clean_text(text))



message_dict = thesis_util.read_pickle(in_path)
print(in_path)
for index, (uid, m) in enumerate(sorted(message_dict.items(), key=sort_key)):
  try:
    handle_message(index, uid, m)
  except:
    errL('error at uid:', uid)
    raise

if is_mode_count:
  errL() # for progress line
  for group, counter in sorted(stats.items()):
    if group.startswith('words from: '):
      continue
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
print('messages used (matched sender and filters):', message_count)
print('messages skipped:', skip_count)
print('phrase matches:', hit_count)
