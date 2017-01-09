#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from os.path import expanduser, join
import argparse
from textwrap import dedent

from CuiList import CuiList, Bold
from RssClient import RssClient
from Pager import pager
from WwwReader import WwwReader
from RssDatabase import RssDatabase

def have_new_items(rssc, rssdb):
    """ Tells you which channel has new items
    """
    new = [any([chdb['new'] for chdb in rssdb.channels[ch['conf']['Name']]])
           for ch in rssc.channels]
    return new
               
def print_channels(cui, rssc, rssdb):
    """ Prints the list of channels
    """
    cui.header = []
    
    # Channels that have unread items
    new = have_new_items(rssc, rssdb)
    
    # Channels which couldn't be updated
    broken = [ch['broken'] for ch in rssc.channels]
    
    flag = lambda n, b: [[' ', '*'][n], '!'][b] + ' '
    cui.items = [flag(n,b) + ch['conf']['Name']
                 for (n, b, ch) in zip(new, broken, rssc.channels)]

def print_items(cui, rssc, rssdb, app):
    """ Prints the list of items for selected channel
    """
    ch = rssc.channels[app.ch_selection] # Selected channel
    conf = ch['conf']
    items = rssdb.channels[conf['Name']]
    
    cui.header = []
    
    # Print title & subtitle if it's intended and if they exist
    # (they may not exist if channel hasn't been updated)
    if ch['rss'].has_key('feed'):
        feed = ch['rss']['feed']
        if int(conf['ShowTitle']):
            if feed.has_key('title'):
                cui.header.append(Bold(feed['title']))
            
        if int( conf['ShowSubtitle']):
            if feed.has_key('subtitle'):
                cui.header.append(feed['subtitle'])
        
    # Append a bland line if title or subtitle is displayed
    if len(cui.header):
        cui.header.append('')
    
    flag = lambda n: [' ', '*'][n] + ' '
    cui.items = [flag(item['new']) + item['title'] for item in items]

def print_content(conf, cui, items):
    """ Prints content of an item
    """
    if int(conf['GetFullText']):
        url = items[cui.selection]['link']
        wr = WwwReader()
        try:
            text = wr.read(url)
        except:
            text = 'Content cannot accessed.'
    else:
        text = items[cui.selection]['summary'].encode('utf-8')
    
    pager(text, cui.display_width)

def key_pressed_cb(key, cui, rssc, rssdb, app):
    """ This callback is called by CUI when a key is pressed
        Some keys (e.g. UpArrow, DownArrow) are handled by the CUI itself, but
        after this, callback is called anyway.
    """
    if key in ['\n', 'KEY_RIGHT']: # Enter
        app.level += 1             # Go one level further
        if app.level == 1:         # Items
            app.ch_selection = cui.selection
            cui.selection = 0
            print_items(cui, rssc, rssdb, app)            

        elif app.level == 2:       # Item's content
            conf = rssc.channels[app.ch_selection]['conf']
            items = rssdb.channels[conf['Name']]
            items[cui.selection]['new'] = False # Mark as read
            cui.disable_curses()
            print_content(conf, cui, items)            
            # Restore list of items
            cui.enable_curses()
            cui.setup_curses()
            app.level = 1
            print_items(cui, rssc, rssdb, app)
    elif key in ['q', 'KEY_LEFT', 'KEY_BACKSPACE']:
        app.level -= 1              # Go one level back
        if app.level == -1:         # Quit
            return True             # Exit CUI
        elif app.level == 0:        # Channels
            print_channels(cui, rssc, rssdb)
            cui.selection = app.ch_selection
    elif key in [' ', 'm']:         # Mark item as read/unread
        if app.level == 1:
            conf = rssc.channels[app.ch_selection]['conf']
            items = rssdb.channels[conf['Name']]
            items[cui.selection]['new'] = not items[cui.selection]['new']
            print_items(cui, rssc, rssdb, app)
    elif key in ['A']:              # Mark all items as read/unread
        if app.level == 1:   
            conf = rssc.channels[app.ch_selection]['conf']
            items = rssdb.channels[conf['Name']]
            new = [item['new'] for item in items]
            val = not any(new)
            for item in items: item['new'] = val
            print_items(cui, rssc, rssdb, app)

class App:
    
    app_version = 1.0
    
    def __init__(self):       
        # CUI levels:
        # -1 - Exit
        #  0 - List of channels
        #  1 - List of items
        #  2 - Content of an item
        self.level = 0        # CUI level
        self.ch_selection = 0 # Currently selected channel

    def parse_args(self):
        """ Parses args of the application
        """
        description = dedent("""
        Lightweight, console based RSS reader
        _______________________________________________________________________
        
        Configuration
        
        For each RSS channel please create separate file in ~/.frss/channels
        Example:
            
        Name           = Some News
        URL            = http://www.somenews.com/rss/example.xml
        GetFullText    = 0
        ShowTitle      = 1
        ShowSubtitle   = 1
        HistoryLength  = 15
        _______________________________________________________________________
        
        Key bindings
        
        ENTER, RIGHT       - Proceed
        BACKSPACE, LEFT, q - Go back or exit
        SPACE, m           - Mark item as read/unread
        A                  - Mark all items as read/unread
        _______________________________________________________________________
        
        """)
        
        parser = argparse.ArgumentParser(description=description, formatter_class=argparse.RawTextHelpFormatter)
        parser.add_argument('-u', '--no-update', action='store_true', help='don\'t update channels')
        parser.add_argument('-x', '--exit', action='store_true', help='exit if there is nothing new')
        parser.add_argument('-V', '--version', action='store_true', help='show version number and exit')
        return parser.parse_args()

    def main(self):
        """ Main function of this application
        """
        args = self.parse_args()
        
        if args.version:
            print 'FRSS v' + str(self.app_version)
            return
        
        # Configure paths
        path_config = join(expanduser('~'), '.frss')
        dir_channels = 'channels'
        path_channels = join(path_config, dir_channels)
        path_db = join(path_config, 'rss.db')
        if not os.path.exists(path_channels):
            os.makedirs(path_channels)
    
        # RSS client reads config files
        rssc = RssClient(path_channels)
        rssc.read_config()

        # Database is restored from the file
        rssdb = RssDatabase(path_db, rssc)
        rssdb.load()
        
        # RSS Client updates data which is merged with the content of Database
        if not args.no_update:
            rssc.update_all()
            rssdb.import_rss()
            rssdb.merge()
            rssdb.save()
    
        # Nothing to be done if all the items are already read
        if args.exit:
            if not any(have_new_items(rssc, rssdb)):
                print 'Nothing new'
                return
    
        # Create and configure CUI
        cui = CuiList()   
        cui.register_cb('key_pressed', key_pressed_cb, [cui, rssc, rssdb, self])

        # Print list of channels
        print_channels(cui, rssc, rssdb)
        
        # Infinite while loop:
        # - displays CUI
        # - waits for the key
        # - handles the key and calls callback
        cui.display()
        
        # Save database to the file
        rssdb.save()




