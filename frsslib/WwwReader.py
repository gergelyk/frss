#!/usr/bin/env python
# -*- coding: utf-8 -*-

#Author: Grzegorz Krason
#webpage: http://krason.biz/#frss

from readability.readability import Document
import requests
from bs4 import BeautifulSoup
import re
import logging


class WwwReader:
    """ Downloads webpage, extracts main content and converts it to text
    """
    
    def __init__(self):
        # Disable messages from 'requests' library
        requests_log = logging.getLogger("requests")
        requests_log.setLevel(logging.WARNING)

    def _download(self, url):
        # Print only host name, not the whole url
        host = re.search('[0-9a-zA-Z\.]+\.[0-9a-zA-Z\.]+', url).group()
        print 'Downloading full text from ' + host + '...'
        
        # Download HTML
        response = requests.get(url, timeout=10)
        return response.content

    def _extract(self, html):
        # Tags to be removed, e.g. '<a>Text<\a>' will be replaced by 'Text'
        tags = ['a', 'strong', 'em']
        for tag in tags:
            pattern = '< ?' + tag + '.*?>(.*?)< ?/' + tag + ' ?>'
            html = re.sub(pattern, '\\1', html, flags=re.I)
        
        return Document(html).summary().encode('utf-8').strip()

    def _html2text(self, html):
        # bold text is going to stay bold (and highlighted)
        # (I know, it's not strict - if sb write _BOLD_1 on the webpage, then
        # we are screwed)
        html = html.replace('<b>', '_BOLD_1')
        html = html.replace('</b>', '_BOLD_0')
        
        # HTML -> text
        soup = BeautifulSoup(html)

        text = soup.get_text('\n').encode('utf-8') # Preserve new lines
        text = text.replace('\t', ' ') # TABs -> space
        text = re.sub(' +', ' ', text) # multiple space -> single space
        text = re.sub('\n{3,}', '\n\n', text) # multiple \n -> double \n
        text = re.sub('^ +', '', text, flags=re.MULTILINE) # remove indents        
        # remove specjal characters at the beginning of the line
        text = re.sub('^[^a-zA-Z]+$', '', text, flags=re.MULTILINE)

        # control characters to make headers bold & highlighted
        text = text.replace('_BOLD_1', '\033[96m\033[1m')
        text = text.replace('_BOLD_0', '\033[0m')
        return text
    
    def read(self, url):
        html = self._download(url)
        html = self._extract(html)
        text = self._html2text(html)
        return text


