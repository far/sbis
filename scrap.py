#!/usr/bin/python
# -*- coding: utf-8 -*-

import textwrap
import HTMLParser
from lxml import html, etree
import requests
import sys
import re
import os
import yaml

# regexp rules

re_link = re.compile('^https?:\/\/([^\/]+)\/(.+)$')
re_link_file = re.compile('^.+\/([^\/]+)\/?$')
re_htmlchar = re.compile('&.+?;')

def error(msg):
    sys.stderr.write('Error: %s\n' % msg)
    sys.exit(1)

# load yaml config

try:
    with open('scrap.yaml') as cfg:
        config = yaml.load(cfg)
except:
    error('Cant load config file')
try:
    link = sys.argv[1].strip()
except:
    error('Usage: scrap.py LINK')

# validate input (url)

res_link = re_link.findall(link)
res_link_file = re_link_file.findall(link)

if not len(res_link) or len(res_link) != 1 or len(res_link[0]) != 2 or not len(res_link_file):
    error('Incorrect URL specified')

domain = res_link[0][0]
fname = res_link_file[0]
if domain not in config['xpath']:
    error('Parser rule doesnt exists for domain {0}'.format(domain))

# make output dir

link_ = re.sub(r"^(?i)https?:\/\/", '', link)
link_.rstrip('/')
if fname.find('.') != -1:
    dirname = config['output_dir'] + '/' + link_[:-1 * len(fname)]
    fname = re.sub(r'\.[^\.]+', '.txt', fname)
else:
    dirname = config['output_dir'] + '/' + link_
    fname = 'index.txt'
try:
    if not os.path.exists(dirname):
        os.makedirs(dirname)
except:
    error("Can't create directory {0}".format(dirname))

# request the page

page = requests.get(link)
if page.status_code != 200:
    error("Can't get response. Status code: {0}".format(page.status_code))

# create DOM tree obj

tree = html.fromstring(page.content)
text = tree.xpath(config['xpath'][domain])
if len(text) != 1:
    error('Error getting data by parser rule')

# strip dirty tags

dom_text = text[0]
etree.strip_tags(dom_text, 'em', 'i', 'pre', 'p', 'h1', 'h2', 'h3', 'strong', 'small', 'a', 'span', 'b', etree.Comment)
etree.strip_elements(dom_text, 'script', 'ul', 'li', 'div', 'table', 'video', with_tail=False)
text = etree.tostring(dom_text)

# remove special HTML chars ( &XXX; )

h = HTMLParser.HTMLParser()
for htmlchar in set(re_htmlchar.findall(text)):
    text = text.replace(htmlchar, h.unescape(htmlchar))

text = re.sub(r'(?i)<BR\s*\/>', '\n', text)
text = re.sub(r'(?i)<[^>]+>', '', text)
text = '\n'.join(['\n'.join(textwrap.wrap(line, config['wrap_width'], break_long_words=False, replace_whitespace=False))
                 for line in text.splitlines() if line.strip() != ''])

# write result to output

with open('{0}/{1}'.format(dirname, fname), 'w') as f:
    f.write(text.encode('utf8'))
