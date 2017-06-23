#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function
from collections import defaultdict
from datetime import datetime
from bs4 import BeautifulSoup
from cookielib import CookieJar
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException,TimeoutException,StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait, Select
import re
import time
import bs4
import simplejson as json
import urllib2

topics_page_url = "http://topics.nytimes.com/top/reference/timestopics/subjects/s/strikes/index.html"


def main():
  browser = webdriver.Firefox()
  browser.get(topics_page_url)

  page_num = 1
  page_max = 4
  data = []
  outname = 'priv'

  with open(outname+'.json','w') as f:
    f.write('[')
    while (page_num <= page_max):
      try:
        print("Going to page", page_num, "...")
        print()
        # Wait until the search area is loaded
        WebDriverWait(browser, 15).until(
          EC.presence_of_element_located((By.XPATH, """//*[@id='searchList']"""))
        )
        if page_num == 1:
          # 
          time.sleep(12)

        i    = 0
        jump = 1

        if page_num == 1:
          source = browser.page_source 
        else:
          while (i < jump):
            link = browser.find_element_by_class_name('next')
            link.click()
            time.sleep(2.5)
            i += 1
          time.sleep(2.5)
          print()
          print("Reading page", page_num, "...")

          # This successfully captures the page source for pages handled by javascript.
          source = browser.execute_script("return document.documentElement.innerHTML;", link)

        stories = get_source(source)
        for si, s in enumerate(stories):
          new_json = get_json(s)
          try:
            t = new_json.get('text')
            print(t)
            new_str = json.dumps(new_json, encoding='utf-8', ensure_ascii=False)
            data = json.loads(new_str)
            f.write(json.dumps(data))

            if t == '':
              print("NO TEXT!")

            # if not t == '' and not si == len(stories)-1:
            #   f.write(', ')
          except Exception, e:
            pass

          if not s == '' and not si == len(stories)-1:
            f.write(', ')

        if not(page_num == page_max):
          f.write(', ')

        page_num += jump

      except (NoSuchElementException,TimeoutException,StaleElementReferenceException):
        pass

    f.write(']')

  time.sleep(2)
  browser.quit()


def get_source(source):
  soup = BeautifulSoup(browser.page_source, "html.parser")
  stories = soup.findAll("div", {"class": "story clearfix"})
  return stories


def make_soup(url):
  # Need to enable cookie.
  cj = CookieJar()
  opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
  html = opener.open(url).read()
  return BeautifulSoup( str(html), "lxml")


def get_json(story):

  def get_story(story_url):
    soup = make_soup(story_url)
    author = soup.find("span", {"class": "byline-author"}).string
    # story = soup.find("div", {"id": "byline-sharetools-container"}).findAll('p')
    # lead_paragraph     = soup.find("p", {"id": "story-continues-1"})
    time.sleep(1)
    # lead_paragraph_str = soup.find("p", class_ = "story-body-text story-content").text
    
    # soup.find("p", {"id": "story-continues-1"}).text
    # for p in soup.find("div", {"id": "story-body"}).findAll("p"):
    #   paragraph_str = ''.join(p.findAll(text=True))

    # if len(lead_paragraph.contents) > 1:
    #   lead_paragraph_str = ' '.join([p.strip() for p in lead_paragraph.contents])
    # else:
    #   lead_paragraph_str = lead_paragraph.contents[0].strip()

    # LeadParagraph = soup.find("p", class_ = "story-body-text story-content")
    LeadParagraph = soup.find("p", {"itemprop": "articleBody"})
    # print(LeadParagraph)

    # Do this hard way.
    LeadParagraphParts = []
    # if len(LeadParagraph.contents) > 1:
    for pi, p in enumerate(LeadParagraph.contents):
      if type(p) is bs4.element.Tag:
        LeadParagraphParts.append(LeadParagraph.contents[pi].text)
      else:
        LeadParagraphParts.append(LeadParagraph.contents[pi])
    LeadParagraphString = ''.join(LeadParagraphParts)
    # elif len(LeadParagraph.contents) == 1:
    #   LeadParagraphString = LeadParagraph.text

    # Removes dateline, e.g., Seoul "--"
    EmDash = u'\u2014'  # same as "\xe2\x80\x94".decode("utf-8")
    if EmDash in LeadParagraphString:
      LPTemp = re.split(EmDash, LeadParagraphString, 1)
      location = LPTemp[0][0:-1]
      LeadParagraphStrNoEmDash = LPTemp[1][1:]
      # LeadParagraphStrNoEmDash = ''.join(LPTemp[1:])
    else:
      LeadParagraphStrNoEmDash = LeadParagraphString

    # print(LeadParagraphStrNoEmDash)
    print()

    return LeadParagraphStrNoEmDash

  try:
    soup = BeautifulSoup(browser.page_source, "html.parser")
    title = story.find("h4").string

    for l in story.findAll('a'):
      if l.parent.name == 'h4':
        link = l["href"]
        print(link)

    author = story.find("div", "byline").string
    summary = story.find("p", "summary").string

    date_raw = story.find("h6", "date").string
  
    date2 = datetime.strptime(date_raw, '%B %d, %Y, %A')
    date = date2.strftime('%Y%m%d')
    
    more_keyword = story.find("div", "moreOn")
    more_dict = defaultdict(list)

    children = more_keyword.findChildren()

    for j in xrange(len(children)):
      more_value = children[j]["value"]
      more_text  = children[j]["href"]
      more_dict[more_value].append(more_text)

    j = json.dumps(more_dict)
    keyword = json.loads(j)
    more_dict.clear()

    text = get_story(link)

    return {'date': date, 'id': 'paraId',  # paraId is dummy variable
            'source': 'NYT', 'summary': summary,
            'text': text,
            'keyword': keyword}

  except Exception, e:
    pass

if __name__ == "__main__":
  main()