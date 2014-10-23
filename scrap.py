#coding=utf8

import textwrap
import HTMLParser
from lxml import html, etree
import requests
import sys
from pprint import pprint
import re
import os

re_link = re.compile('^https?:\/\/([^\/]+)\/(.+)$')
re_link_file = re.compile('^.+\/([^\/]+)\/?$')
re_htmlchar = re.compile('&.+?;')

# main output directory
OUTPUT_DIR = "output"

PARSER_XPATH = {
    'lenta.ru'          : '//div[@itemprop="articleBody"]',
    'www.gazeta.ru'     : '//div[@class="text"]',
    'rg.ru'             : '//div[@class="main-text"]',
    'lifenews.ru'       : '//div[@class="note"]',
    'www.aif.ru'        : '//article[@class="articl_body content_text bottom_dotted clearfix"]',
    'www.utro.ru'       : '//div[@class="article-txt _ga1_on_"]',
    'www.kommersant.ru' : '//div[@id="divLetterBranding"]',
}

try:
    link = sys.argv[1].strip()
except:
    print "\nscrap.py LINK"
    sys.exit(0)

print "LINK: {0}".format(link)
res_link = re_link.findall(link)
res_link_file = re_link_file.findall(link)

if not len(res_link) or len(res_link) != 1 or len(res_link[0]) != 2 or not len(res_link_file):
    print "Incorrect URL specified"
    sys.exit(0)

domain = res_link[0][0]
fname = res_link_file[0]

if domain not in PARSER_XPATH:
    print "Parser rule doesnt exists for domain {0}".format(domain)
    sys.exit(0)

link_ = re.sub(r"^(?i)https?:\/\/", "", link)
link_.rstrip("/")
if fname.find(".") != -1:
    dirname = OUTPUT_DIR+"/"+link_[:-1*len(fname)]
    fname = re.sub(r'\.[^\.]+', '.txt', fname)
else:
    dirname = OUTPUT_DIR+"/"+link_
    fname = 'index.txt'

try:
    if not os.path.exists(dirname):
        os.makedirs(dirname)
except:
    print "Can't create directory {0}".format(dirname)
    sys.exit(0)
    
page = requests.get(link)
if page.status_code != 200:
    print "Can't get response. Status code: {0}".format(page.status_code)
    sys.exit(0)

tree = html.fromstring(page.content)
text = tree.xpath(PARSER_XPATH[domain])
if len(text) != 1:
    print "Error getting data by parser rule"
    sys.exit(0)

dom_text = text[0]
etree.strip_tags(dom_text, 'em', 'i', 'pre', 'p', 'h1', 'h2', 'h3', 'strong', 'small', 'a', 'span', 'b', etree.Comment)
etree.strip_elements(dom_text, 'script', 'ul', 'li', 'div', 'table', 'video', with_tail=False)

text = etree.tostring(dom_text)

# remove HTML chars ( &XXX; )
h = HTMLParser.HTMLParser()
for htmlchar in set(re_htmlchar.findall(text)):
    text = text.replace(htmlchar, h.unescape(htmlchar))

text = re.sub(r'(?i)<BR\s*\/>', '\n', text)
text = '\n'.join([ "\n".join(textwrap.wrap(line, 80, break_long_words=False, replace_whitespace=False)) for line in text.splitlines() if line.strip()!=""])

with open("{0}/{1}".format(dirname, fname), "w") as f:
    f.write(text.encode('utf8'))



