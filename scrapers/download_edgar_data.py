#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
A simple code that downloads publicly available filing documents from
SEC EDGAR
https://www.sec.gov/edgar/searchedgar/companysearch.html
"""
from __future__ import print_function
from bs4 import BeautifulSoup as bs
import multiprocessing
import os
import re
import signal
import time
import urllib2
import constants

_manager = multiprocessing.Manager()
_main_lock = multiprocessing.Lock()
_writer_lock = multiprocessing.Lock()


def get_docs_data(cik, filing_type):
    """
    Get all tuples of filing document url, filing year, and file extension
    for given CIK and filing type (e.g., 10-K or DEF 14A)
    """
    company_url = '{}action=getcompany&CIK={}&type={}&count=100'
                  .format(constants.EDGAR_BASE_URL, cik, filing_type)

    soup = bs(urllib2.urlopen(company_url), 'lxml')
    search_result = []
    for a in soup.find_all('a', href = re.compile(r'/Archives.*')):
        filing_detail_page_url  = constants.SEC_BASE_URL + a['href']
        filing_type = a.parent.find_previous_sibling('td').text.replace(' ', '+')
        filing_date = a.parent.find_next_siblings('td')[1].get_text()
        if int(filing_date.split('-')[0]) > 2005:
            search_result.append((filing_detail_page_url, filing_type, filing_date))

    # List of dictionaries
    filing_details_all_years = []

    for url, type, date in search_result:
        filing_dic = {}
        soup = bs(urllib2.urlopen(url), 'lxml')
        htm = soup.find('a', href=re.compile(r'/Archives.*.htm'))
        # Older documents are only available in .txt
        # Complete submission text file is at the bottom
        doc = soup.find_all('a', href=re.compile(r'/Archives.*.txt'))[-1]

        filing_dic['url']  = constants.SEC_BASE_URL + doc['href']
        filing_dic['type'] = type
        filing_dic['date'] = date
        filing_dic['save_ext'] = 'html' if htm else 'txt'

        filing_details_all_years.append(filing_dic)

    return filing_details_all_years


def is_cik_valid(cik):
    if not cik: return False
    if int(cik) == 0: return False

    return True


def get_raw_data(name, cik, dictionary):
    """
    Open up filing document and save content as desired file type
    (html or txt).

    TODO: Search, in each document, strings like `fiscal YYYY year` or
    `fiscal year end(ed)`
    """
    _main_lock.acquire()

    url      = dictionary['url']
    type     = dictionary['type']
    date     = dictionary['date']
    save_ext = dictionary['save_ext']

    path_to_company_directory = os.path.join(constants.RAW_DATA_PATH,
                                             '{}_{}'.format(name, cik))
    if not os.path.exists(path_to_company_directory):
        os.mkdir(path_to_company_directory)

    path_to_file = os.path.join(path_to_company_directory,
                    '{0}_{1}_{2}.{3}'.format(cik, type, date, save_ext))

    if (url is not None and not os.path.exists(path_to_file)):
        raw_data = urllib2.urlopen(url, timeout = 9999).read()
        write_data(raw_data, path_to_file)

    _main_lock.release()

    # return raw_data


def write_data(data, path_to_file):
    """
    Write data to result file
    """
    _writer_lock.acquire()

    os.path.exists(path_to_file)
    if not os.path.exists(path_to_file):
        # Save source code text as html will do the same job as downloading
        # the .htm directly
        # To use urllib.urlretrieve, further changes to the code must be made.
        with open(path_to_file, 'w') as f:
            f.writelines(data)

    _writer_lock.release()


def get_name_key_pair(info):
    """
    Convert company info to web query and get CIK
    """
    if info.split('#')[0].isdigit():
        cik  = info.split('#')[0]
        url  = '{}action=getcompany&CIK={}'.format(constants.EDGAR_BASE_URL, cik)
        soup = bs(urllib2.urlopen(url), 'lxml')
        name = soup.find('span', 'companyName').get_text().split('CIK#')[0].strip()

        return cik, name

    else: 
        adict = {r'/': r'%2F', r',': r'%2C', r'&': r'%26', r' ': r'+'}
        query = multiple_replace(info, adict)
        url = '{}&action=getcompany&company={}'.format(constants.EDGAR_BASE_URL, query)
        print(url)
        soup = bs(urllib2.urlopen(url), 'lxml')

        try:
            multiple_results_exist = soup.find('span', 'companyMatch')

            if multiple_results_exist is not None:
                return '0', ''
            else:
                tag = soup.find('span', 'companyName')
                if tag:
                    text = tag.text.encode('utf-8').strip()
                    # AXCELIS TECHNOLOGIES INC CIK#: 0001113232 (see all company filings)
                    cik = re.match(r'.*CIK#: (\d+)', text).group(1)
                    # Return query as well since / is allowed in directory name
                    return cik, query
                else:
                    return '0', ''
        except AttributeError:
            return '0', ''


def get_company_filing_data_all_years(line):
    """
    Get company CIK and download filing documents for all years
    """
    cik, query = get_name_key_pair(line)
    print('{}: CIK# {}'.format(query, cik))

    if is_cik_valid(cik):
        for t in ['DEF+14A', 'DEFM', 'DEFR', 'DEFC']:  # filing type
            for dict in get_docs_data(cik, t):
                get_raw_data(query, cik, dict)


def multiple_replace(string, adict):
    rx = re.compile('|'.join(adict.keys()))
    query = rx.sub(lambda m: adict[m.group(0)], string)

    return query


def init_worker():
    signal.signal(signal.SIGINT, signal.SIG_IGN)


def main():
    if not os.path.exists(constants.RAW_DATA_PATH):
        os.mkdir(constants.RAW_DATA_PATH)

    # Use # to comment out companies to skip.
    with open(constants.COMPANY_NAME_FILE) as f:
        companies = filter(None, [l.rstrip('\n') for l in f.readlines() if not l.startswith('#')])
    # print(companies)

    pool = multiprocessing.Pool(4, init_worker)

    try:
        result = pool.map_async(get_company_filing_data_all_years, companies)
        result.get(timeout = 999999)
        time.sleep(5)
        pool.close()
        pool.join()

    except KeyboardInterrupt:
        print("Terminating workers.")
        pool.terminate()
        pool.join()


if __name__ == '__main__':
    start_time = time.time()
    main()
    print('Elapsed time:', time.time() - start_time, 'seconds.')
