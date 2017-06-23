#!/usr/bin/env python
#-*- coding: utf-8 -*-
from __future__ import print_function
from bs4 import BeautifulSoup as bs
from selenium import webdriver
import multiprocessing
import os
import re
import signal
import sys
import time
import csv
import urllib2
import constants


def worker(lock, queue, monitor):
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

        search_url = 'http://www.bing.com/search?q=%2bsite%3alinkedin.com+' + query
        browser = webdriver.Firefox()
        browser.implicitly_wait(4)
        browser.get(search_url)

        if browser.find_elements_by_xpath("//li[@class='b_no']"):
            result = 'No results found for {}. He/She is probably not a CEO.'.format(query)

        else:
            links = browser.find_elements_by_xpath("//li[@class='b_algo']/h2/a[@href]")
            url = next((link.get_attribute('href') for link in links
                        if 'linkedin.com/in/' in link.get_attribute('href')), None)

            if url:
                req  = urllib2.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                page = urllib2.urlopen(req).read()
                soup = bs(page, 'lxml')

                try:
                    name = soup.find('h1', attrs = {'id': 'name'}).text.encode('utf-8').strip()
                    tag = soup.find('section', attrs = {'id': 'experience'})
                    roles = [t.text.encode('utf-8').strip() for t in tag.find_all('h4', attrs={'class':'item-title'})]
                    companies = [t.text.encode('utf-8').strip() for t in tag.find_all('h5', attrs={'class':'item-subtitle'})]
                    date_ranges = [t.text.encode('utf-8').strip() for t in tag.find_all('span', attrs={'class':'date-range'})]
                    positions = []

                    for i in range(len(roles)):
                        dates = date_ranges[i].split('(')[0].split('\xe2\x80\x93')  # split date range by en dash
                        start_date = dates[0].strip()
                        end_date   = dates[1].strip() if len(dates) == 2 else ''
                        positions.append({'company': companies[i],
                                          'role': roles[i],
                                          'start_date': start_date,
                                          'end_date':   end_date})

                    with lock:
                        with open('linkedin.csv', 'ab') as csvfile:  # append
                            writer = csv.writer(csvfile, dialect = 'excel')
                            writer.writerow([name])
                            writer.writerow(['Company', 'Role', 'Start Date', 'End Date'])
                            for p in positions:
                                result = [p['company'], p['role'], p['start_date'], p['end_date']]
                                # print(result)
                                writer.writerow(result)

                except AttributeError:
                    result = 'WARNING: Something went wrong. Check out ' + url

            else:
                with lock:
                    writer.writerow(result)

        browser.quit()


def main():

    manager = multiprocessing.Manager()
    lock = manager.Lock()
    monitor = manager.dict()
    queue = manager.Queue()

    with open(constants.SEARCH_STRING_FILE) as f:
        lines = filter(None, [line.rstrip('\n') for line in f.readlines()
                            if not line.startswith('#')])

    # alist = [r',', r'\w\.', r'/\w+/?']
    # # Join all the regexes
    # rx = re.compile('|'.join(alist), re.M|re.DOTALL)
    # queries = [re.sub(r'\s+', r'+', rx.sub(r'', line)) for line in lines]
    queries = [re.sub(r'\s+', r'+', line) for line in lines]
    for query in queries:
        queue.put(query)

    pool = multiprocessing.Pool(4, worker, (lock, queue, monitor))
    while True:
        try:
            time.sleep(1)
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