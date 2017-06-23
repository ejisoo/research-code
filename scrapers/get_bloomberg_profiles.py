#!/usr/bin/env python
#-*- coding: utf-8 -*-
from __future__ import print_function
from bs4 import BeautifulSoup as bs
from selenium import webdriver
import multiprocessing
import optparse
import os
import re
import signal
import sys
import time
import urllib2
import constants


def worker(lock, queue, monitor, filename):
    """
    """
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    pid = os.getpid()
    while True:
        waiting = True
        try:
            monitor[pid] = waiting
            query = queue.get()
        except (IOError, EOFError):
            return
        monitor[pid] = False
        search_url = 'http://www.bing.com/search?q=site%3abloomberg.com+' + query + '+"executive%20profile"'
        # search_url = 'http://www.bing.com/search?q=%2bsite%3abloomberg.com+' + query
        print(search_url)
        browser = webdriver.Firefox()
        browser.get(search_url)
        time.sleep(2)

        # Use Bing
        if browser.find_elements_by_xpath("//li[@class='b_no']"):
            # No results
            text = 'No results found for {}. He/She is probably not a CEO.'.format(query)
        else:
            links = browser.find_elements_by_xpath("//li[@class='b_algo']/h2/a[@href]")
            url, output = '', ''
            url_patterns = ['bloomberg.com/research/stocks/private/person',
                            'bloomberg.com/research/stocks/people/person']
            # Get the first match
            url = next((link.get_attribute('href') for link in links
                        if any(pat in link.get_attribute('href').lower()
                            for pat in url_patterns)), None)

            if url:
                soup = bs(urllib2.urlopen(url), 'lxml')
                try:
                    # Get director name and background
                    name = soup.find_all('h1', attrs = {'itemprop': 'name'})[0].get_text()
                    bio = soup.find(itemprop = 'description').get_text().encode('utf-8').strip()
                except AttributeError:
                    print('WARNING: Something is wrong. Check out ' + url)

            relationship = next((link.get_attribute('href') for link in links
                        if 'bloomberg.com/research/stocks/people/relationship' in link.get_attribute('href').lower()), None)

            url = next((link.get_attribute('href') for link in links
                        if 'bloomberg.com/profiles/people' in link.get_attribute('href').lower()), None)

            if url:
                soup = bs(urllib2.urlopen(url), 'lxml')
                try:
                    name = soup.find('h1', attrs = {'class': 'name'}).get_text()
                    history = re.sub(r'\n{2,}', r'\n', soup.find(True,
                        attrs = {'class': 'markets_module bio_career'}).get_text().encode('utf-8').strip())
                except AttributeError:
                    print('WARNING: Something is wrong. Check out ' + url)

            if not output:
                text = "WARNING: Could not find anything. Check out {}".format(search_url)

        with lock:
            with open(filename, 'a+') as f:
                f.write('# %s\n\n' % name)
                if relationship: f.write('%s\n\n' % relationship)
                if bio: f.write('%s\n\n' % bio)
                if history: f.write('%s\n\n' % history)
                f.write('\n\n')
                f.flush()

        browser.quit()


def main():
    parser = optparse.OptionParser()
    parser.add_option('-I', '--input', dest='input')
    parser.add_option('-O', '--output', dest='output')
    options, remainder = parser.parse_args()

    manager = multiprocessing.Manager()
    lock = manager.Lock()
    monitor = manager.dict()

    queue = manager.Queue()

    with open(options.input) as f:
        lines = filter(None, [line.rstrip('\n') for line in f.readlines()
                            if not line.startswith('#')])

    queries = [re.sub(r'\s+', r'+', line) for line in lines]

    for query in queries:
        queue.put(query)

    pool = multiprocessing.Pool(4, worker, (lock, queue, monitor, options.output))

    while True:
        try:
            time.sleep(2)
            waits = []
            pids = iter(monitor.keys())
            for p in pids:
                waits.append(monitor[p])
            if all(waits):
                pool.terminate()
                pool.join()
                return
        except KeyboardInterrupt:
            pool.terminate()
            pool.join()
            sys.exit()


if __name__ == '__main__':
    start_time = time.time()
    main()

    print('Elapsed time:', time.time() - start_time, 'seconds.')

