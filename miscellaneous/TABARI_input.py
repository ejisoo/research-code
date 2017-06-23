#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function
from lxml import etree
import re

path = 'TABARI.0.8.4b2.OSX.dir/'
infile  = './hunger.xml'
outfile = 'test'
parser = etree.XMLParser(remove_blank_text=True)

t = etree.parse(infile, parser)
root = t.getroot()
sent_data = root.findall('Sentence')
text_data = root.findall('Sentence/Text')

with open(path + outfile, 'w') as f:

  for s, d in zip(sent_data, text_data):
    string = etree.tostring(s, encoding='utf-8')
    date = string.split("date=")[1][3:9]
    pid  = string.split("id=")[1][1:9]
    print(date, pid, file=f)
   
    text   = etree.tostring(d, encoding='utf-8')
    
    words_list    = text.split("<Text>")[1].split("</Text>")[0].split()
    # [' '.join(words_list[nn*i: nn*i + nn]) for i in xrange(0, len(words_list)/nn+1)] # nn = 9
    words_regroup = []
    loop = 1
    start = 0
    nchar = 60.
    lmax = ceil(len(''.join(words_list))/nchar)

    while loop <= lmax:
      size  = 0
      for i in range(len(words_list))[start:]:
        size += len(words_list[i])
        if size > nchar:
          g = ' '.join([item for item in words_list[start:i]])
          start = i
          break
        elif loop == lmax:
          g = ' '.join([item for item in words_list[start:]])
        else:
          pass
      words_regroup.append(g)
      loop += 1
  
    result = '\n'.join(words_regroup)

    print(result, file=f)
    print('', file=f)