#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function
import argparse
import itertools
import os
import subprocess
import time
from lxml import etree


def handle_commandline():
    aparse = argparse.ArgumentParser()
    aparse.add_argument('-i', '--inputs', required=True, nargs='*',
            help='result file and xml file')
    aparse.add_argument('-o', '--output', required=True)
    aparse.add_argument('-p', '--data')
    args = aparse.parse_args()
    return args.inputs, args.output, args.data


def do_shell(line):
    proc = subprocess.Popen(line, shell=True, stdout=subprocess.PIPE)
    output = proc.communicate()[0]
    return output


if __name__ == '__main__':
    start = time.time()
    input_files, output_file, data_path = handle_commandline()
    all_lines = []
    for i, file in enumerate(input_files):
        with open(file) as f:
            lines = f.readlines()
        all_lines = all_lines + lines

    stream = open(output_file, 'wb')
    all_events = []
    for line in all_lines:
        event = line.split()
        sent_id = event[-2]
        story_date = event[0]
        if event[3].isdigit():
            event_code = event[3]
            all_events.append((event_code, sent_id))

    by_code = lambda x: x[0]
    d = {k: list(v) for k, v in itertools.groupby(sorted(all_events), by_code)}
    all_codes = d.keys()
    for code in sorted(all_codes):
        print('Code:  {}'.format(code))
        for ti, t in enumerate(d[code]):
            # f_path = os.path.join(data_path, 'test*.xml')
            # line = 'grep -A 4 {} {}'.format(t[1], f_path) #--no-filename 
            line = 'grep -r -A 4 --no-filename {} {}'.format(t[1], data_path)
            output = do_shell(line)
            file_match = output.split('\n')[0].split('<Sentence')[0]
            stream.write('<!-- VERB CODE: {} -->\n'.format(code))
            for ri, r in enumerate(output.split('\n')):
                stream.write('{}\n'.format(r))
            # stream.write('<!-- VERB CODE: {} // {} -->\n'
            #     .format(code, os.path.basename(file_match[:-1])))
            # for ri, r in enumerate(output.split('\n')):
            #     stream.write('{}\n'.format(r[len(file_match):]))

    print('Done in {:.3f} seconds'.format(time.time() - start))

