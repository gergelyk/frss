#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pickle
import os.path


class RssDatabase:
    """ Collects data from RSS client and from previous session. Decides
        which items are new and wihch should be discarded
    """
    def __init__(self, path_db, rssc):
        self.path_db = path_db
        self.rssc = rssc
        
        # RSS data is stored in dictionaries. Key is the channel name. Value is
        # the list of the items.
        self.channels = {}     # self.channels merged with previous session
        self.new_channels = {} # channels imported from RSS client

    
    def import_rss(self):
        channels = {}
        for ch in self.rssc.channels:
            # Check how many items should be displayed for each channel
            name = ch['conf']['Name']
            hist_len = int(ch['conf']['HistoryLength'])
            
            # Copy items from RSS client (only meaningful data)
            items = [{k: item[k] for k in ('title', 'link', 'summary')}
                     for item in ch['rss']['items']]
            
            # Clip the list of items
            channels[name] = items[:hist_len]

        self.new_channels = channels
        
    def save(self):
        """ Saves current RSS content to a file
        """
        with open(self.path_db, 'wb') as f:
            pickle.dump(self.channels, f)
            
    def load(self):
        """ Loads RSS content from the previous session from a file
        """
        if os.path.isfile(self.path_db):
            with open(self.path_db, 'rb') as f:
                self.channels = pickle.load(f)

    def merge(self):
        # 'new' flag equals True if an item hasn't been read, otherwise it is False
    
        # k is a key = channel name as defined in config
        # channels with the same name are considered the same
    
        # items are considered the same if they belong to the same channel and
        # their 'link' fields are equal
    
        for k in self.new_channels:
            if k in self.channels: # channel already exists in the previous session
                
                # Review new items
                links = [item['link'] for item in self.channels[k]]
                for i in range(len(self.new_channels[k])):
                    if self.new_channels[k][i]['link'] not in links:
                        # If an item didn't exist in the previous session,
                        # mark it as new
                        self.new_channels[k][i]['new'] = True
                    else:
                        # If an item existed in the previous session,
                        # copy 'new' flag from that session
                        index = links.index(self.channels[k][i]['link'])
                        self.new_channels[k][i]['new'] = self.channels[k][index]['new']

                # Review old items
                links = [item['link'] for item in self.new_channels[k]]
                for i in range(len(self.channels[k])):
                    # if an item is not provided by RSS client, it is considered
                    # historical and it should be added to the list of items as it is
                    if self.channels[k][i]['link'] not in links:
                        self.new_channels[k].append(self.channels[k][i])

                # Check how many items should be displayed for each channel
                # and clip the list accordingly
                i = [ch['conf']['Name'] for ch in self.rssc.channels].index(k)
                hist_len = int(self.rssc.channels[i]['conf']['HistoryLength'])
                self.new_channels[k] = self.new_channels[k][:hist_len]
                
            else: # new channel added to the config directory            
            
                # mark all the items as new
                for item in self.new_channels[k]:
                    item['new'] = True
                    
        self.channels = self.new_channels

                
