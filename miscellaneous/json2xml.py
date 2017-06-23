#!/usr/bin/env python
from __future__ import print_function
import argparse
import multiprocessing
import os
import pickle
import sys
import time
import nltk.data
import simplejson as json
import ujson
from xml.etree import ElementTree as et
from xml.etree.ElementTree import parse, tostring, Element, iterparse
from xml.sax.saxutils import escape, unescape
from lxml import etree
from nltk.tokenize import RegexpTokenizer
from nltk import tokenize
from dict2xml import dict2xml as xmlify

reload(sys)
sys.setdefaultencoding('utf-8')


def handle_commandline():
    aparse = argparse.ArgumentParser()
    aparse.add_argument('input')
    args = aparse.parse_args()
    return os.path.abspath(args.input)


class JSONObject:
    def __init__(self, d):
        self.__dict__ = d


def json_to_dict(filename):
    stream = open(temp_path, 'w')
    stream.write('[')
    raw_data = json.loads(open(filename, 'r').read(), object_hook=JSONObject)
    indices = [di for di, d in enumerate(raw_data) if not(d.text == '')]
    last_nonempty_entry_id = indices[-1]
    print('Total number of episodes: {}'.format(len(raw_data)))
    # print('Last empty text occurs at episode {}'.format(indices[-1]))
    for di, d in enumerate(raw_data):
        if any([s.isalpha() for s in d.text.split()]):
        # if bool(d.text.replace('<>', '').strip()):
            date = d.date.replace('-', '')
            # para_text = (d.text, d.text[6:])[d.text.startswith('LEAD:')]
            para_text = (d.text.startswith('LEAD:')) and d.text[6:] or d.text
            # para_text = (d.text.startswith('To the LEAD:')) and d.text[6:] or d.text
            sent_data = tokenizer.tokenize(para_text)
            chunk = []
            d.text.replace
            for si, s in enumerate(sent_data):
                new_id = d.id + '_' + str(si+1)
                # del d.id
                w = dict()
                w.update({'date': date, 'id': new_id, 'text': s})
                chunk.append(ujson.dumps(w))
            stream.write(', \n'.join(chunk))
            if not(di == last_nonempty_entry_id):
                stream.write(',\n')
            stream.flush()
    # stream.write(', '.join([json.dumps(d.__dict__) for d in raw_data]))
    stream.write(']')


def dict_to_xml(tag, d):
    '''
    Convert dict of key/value pairs into XML
    '''
    elem = Element(tag)
    for key, val in d.items():
        child = Element(key)
        child.text = str(val)
        elem.append(child)
    return elem


def xml_formatter(inname, outname):
    '''
    Format XML for petrarch
    Escape special characters and removes blank space
    '''
    data = json.loads(open(inname).read())
    stream = open(outname, 'wb')
    stream.write('<Sentences>\n\n')
    for di, d in enumerate(data):
        e = dict_to_xml('Sentence', d)
        start_sent = ' '.join([e.tag] +
            ['{0}="{1}"'.format(child.tag, child.text)
            for child in e.getchildren() if not (child.tag == 'text')])
        text = escape(e.find('text').text).replace('\n\t\t', '').replace(
            '&lt;&gt;', '')
        stream.write(
            '\n'.join(['<{} source="NYT" sentence="True">'.format(start_sent),
            '<Text>\n{}\n</Text>'.format(text), '</Sentence>\n\n'])
            )
        stream.flush()
    stream.write('</Sentences>')
    stream.close()


def main():
    global inpath
    global parser, tokenizer
    global temp_path

    start = time.time()

    extra_abbrev = ['dr', 'vs', 'mr', 'ms', 'mrs', 'prof', 'inc',
        'i.e', 'g.m', 'no', 'gov', 'm.t.a', 'c.i.a']
    tokenizer = nltk.data.load('tokenizers/punkt/english.pickle')
    tokenizer._params.abbrev_types.update(extra_abbrev)

    inpath = handle_commandline()
    dirname = os.path.dirname(inpath)
    outpath = os.path.splitext(inpath)[0] + '.xml'
    temp_path = os.path.splitext(inpath)[0] + '.tmp'

    json_to_dict(inpath)
    print('JSON converted to dictionary!  Took {} seconds'.format(
        time.time()-start))
    
    parser = etree.XMLParser(encoding='utf-8', recover=True,
        remove_blank_text=True, ns_clean=True)
    xml_formatter(temp_path, outpath)
    print('All done!')
    print('Total elapsed time: {0:.3f} seconds'.format(time.time() - start))


if __name__ == '__main__':
    main()