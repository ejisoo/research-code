#!/usr/bin/env python
# -*- coding: utf-8 -*-
# This script removes the clutter produced by MATLAB (and its parpool)
# command:
#   python clean_out.py --source=<SOURCE DIR> --extension=out -R
#   python clean_out.py -i <INPUT FILE> -o <OUTPUT FILE>
from __future__ import print_function
import argparse
import os
import re
import sys
import time


def main():
    start = time.time()
    infile_list, outfile, source, ext, redo = handle_commandline()
    
    if source:  # override in_file when source is specified
        # abs_source = os.path.abspath(source)
        abs_source = source
        out_files = [f for f in os.listdir(abs_source) if (f.endswith(ext) and not '_clean' in f)]
        print('out files')
        print(out_files)
        if not redo:
            # do not include already-cleaned files
            cleaned = []
            for f in os.listdir(abs_source):
                if '_clean' in f:
                    cleaned.append('{}.{}'.format(f.split('_clean')[0], ext))
            to_clean = list(set(out_files) - set(cleaned))
            print('already cleaned')
            print(cleaned)
        else:
            to_clean = out_files

    alist = [
        r'\[\x08.*?\x08\s*',
        r'>>\s*',  # MATLAB parpool
        r'\s*Starting.*?\.\.\.\s*',
        r'\s*connected to.*?workers\.\s*',
        r'\s*-{10,}\s*',  # MATLAB license warning
        # MATLAB license warning
        # They are gone now (October 1X, 2015) 
        # r'\s*----------------------------------------------------\s*', 
        # r'\s*Your MATLAB license will expire in \d+ days\.\s*',        
        # r'\s*Please contact your system administrator or\s*',
        # r'\s*MathWorks to renew this license\.\s*',
        r'\s*< M A T L A B \(R\) >\s*',  # MATLAB welcome message
        r'\s*Copyright 1984-2014 The MathWorks, Inc.\s*',
        r'\s*R2014b \(8.4.0.150421\) 64-bit \(glnxa64\)\s*',
        r'\s*September 15, 2014\s*',
        r'To get started, type one of these: helpwin, helpdesk, or demo\.\s*',
        r'For product information, visit www\.mathworks\.com\.\s*',
        r'ans\ =\n\n\s*\d+\.?\d*.*?$',   # quick fix
        r'srun: Force Terminated.*?$',
        r'Your MATLAB session has timed out.  All license keys have been returned.'
    ]

    # Join all the regexes
    rx = re.compile('|'.join(alist), re.M|re.DOTALL)

    if source:
        if to_clean:
            for f in to_clean:
                inname = os.path.join(source, f)
                outname = os.path.join(source, os.path.splitext(f)[0] + '_clean.log')
                clean_out(inname, outname, rx)
                print('Elapsed time: {:.3f} seconds'.format(time.time() - start))
        else:
            print('Nothing to clean. Program exiting..')
    elif infile_list[0]:
        # if outfile:  # custom output name
        #     clean_out(in_file, outfile, rx)
        # # default option appends `_clean` at the end
        # else:
        if True:  # just to keep indentation for now
            for fi, f in enumerate(infile_list):
                print('Processing file {}/{}'.format(fi + 1, len(infile_list)))
                clean_out(f, os.path.splitext(f)[0] + '_clean.log', rx)
        print('Total elapsed time: {:.3f} seconds'.format(time.time() - start))


def handle_commandline():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input', nargs='+', required=True,
            help='List input files separated by space. Requires at least one argument.')
    parser.add_argument('-o', '--output')
    parser.add_argument('--source', nargs='?')
    parser.add_argument('--extension', default='out')
    parser.add_argument('-R', '--redo', action='store_true', default=False,
            help='Clean all again. Overwrite already-cleaned files if any.')
    args = parser.parse_args()

    return args.input, args.output, args.source, args.extension, args.redo


def clean_out(inname, outname, rx):
    with open(inname, 'rt') as infile:
        string = infile.read()
    
    with open(outname, 'w') as outfile:
        # doing this way gives more readable log
        # replace by newline first and then remove redundant newlines
        stripped = rx.sub(r'\n', string)
        stripped = re.sub(r'\n{3,}', r'\n\n', stripped)
        outfile.write(stripped)

        # striped = re.split(r'(Build simSum:.*\n\n)', stripped)
        # # move kappa_phi
        # rx_move = re.compile(r'(^.*)(kappa_phi =\n\n(?:\s+Columns \d{1,2} through \d{1,2}\n\n(?:\s+\d+\.\d+){3}\n\n){5})(.*$)', re.DOTALL)
        # moved = rx_move.sub(r'\2\1\3', striped[-1])
        # reordered = striped[0].lstrip('\n') + striped[1] + moved
        # outfile.write(reordered)


if __name__ == '__main__':
    main()