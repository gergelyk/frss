#!/usr/bin/env python
# -*- coding: utf-8 -*-

from configobj import ConfigObj
from os.path import join
from os import walk
from copy import deepcopy
import feedparser

class RssClient:
    """Reads configuration of the channels and downloads RSS content
    """

    def __init__(self, path_channels):        
        # Find all config files
        self.path_channels = path_channels
        _, _, self.file_names = walk(path_channels).next()

        # Prepare default channel configuration
        default_values = dict(
        GetFullText    = 0,
        ShowTitle      = 1,
        ShowSubtitle   = 1,
        HistoryLength  = 15,
        )
        self.ch_init_conf = ConfigObj(default_values)        
        
    def read_config(self):
        self.channels = []
        for file_name in self.file_names:
            # Initialize with default values
            ch_conf = deepcopy(self.ch_init_conf)
            
            # Update with actual values
            ch_conf.update(ConfigObj(join(self.path_channels, file_name)))
            
            # conf - configuration from the config file
            # rss - content downloaded from RSS channel
            self.channels.append({'conf': ch_conf, 'rss': {}, 'broken': False})
            
    def update_all(self):
        # Download content of RSS channels
        for ch in self.channels:
            print 'Updating ' + ch['conf']['Name'] + '...'
            rss = feedparser.parse(ch['conf']['URL'])
            ch['rss'] = rss
            broken = rss['feed'] == {}
            ch['broken'] = broken
            if broken:
                print ' FAILED'

        
