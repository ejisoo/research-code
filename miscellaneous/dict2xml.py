#!/usr/bin/env python
from __future__ import print_function
try:
	import ujson as json
except ImportError:
	import simplejson as json
import pickle
import nltk.data
import re
import time
from lxml import etree
from dict2xml import dict2xml as xmlify
from nltk.tokenize import RegexpTokenizer
from nltk import tokenize

dirname = './'
input_file = 'xx'

start = time.time()
data = json.loads(open(input_file+'.json').read())

with open(dirname + input_file + '.xml', 'w') as x:
	print("<Sentences>", file=x)
	for di, d in enumerate(data):
		e = xmlify(d, wrap="Sentence", newlines=True)  # indent="  "
		print(e)
		print(e.encode('utf-8'), file=x)
	print("</Sentences>", file=x)

parser = etree.XMLParser(remove_blank_text=True)
tree = etree.parse(dirname + input_file + '.xml', parser)

elem_date = tree.findall('.//date')
elem_id = tree.findall('.//id')

xslt = etree.parse('../xslt/nyt_topics.xslt')

transform = etree.XSLT(xslt)
newtree = transform(tree)

newtree.write(dirname + input_file + '_pp.xml', encoding="utf-8", pretty_print=True)

#####

test_file = dirname + input_file + '_pp.xml'

with open('xxx.xml', 'w') as y:

  t = etree.parse(test_file, parser)
  root = t.getroot()

  data = root.findall('Sentence')
  # print(data)

  print("<Sentences>", file=y)
  for di, d in enumerate(data):
    string = tostring(data[di], encoding='utf-8').replace("\xe2\x80\x99", "'").replace("\xe2\x80\x9c", '"').replace("\xe2\x80\x9d", '"').replace("\xc3\xa1", "a").replace("\xe2\x80\x94", "-")
    print(string, file=y)
  print("</Sentences>", file=y)

tp = etree.parse('xxx.xml', parser)
tp.write('xxx_pp.xml', encoding="utf-8", pretty_print=True)

end = time.time()
print('Total time: ', end - start)