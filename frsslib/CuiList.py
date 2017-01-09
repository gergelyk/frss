#!/usr/bin/env python
# -*- coding: utf-8 -*-

import locale
import curses

class PrintingError(Exception):
    """Exception raised when curses cannot print text
    """
    def __init__(self, error, y, x, text):
        Exception.__init__(self, 'Printing error [y: ' +
                           str(y) + ', x: ' + str(x) +
                           ', text: \'' + text +
                           ', msg: ' + error.message + '\']')

class CuiList():
    """Engine, manages CUI
    """
    def __init__(self):
        self.display_width  = 0     # terminal width
        self.display_height = 0     # terminal height
        self.callback = {}
        self.callback_args = {}
        self.scroll = 0             # number of lines the page is shifted by
        self.selection = 0          # item to be highlighted (or None)
        self.page_size = 5          # PageDown, PageUp behaviour
        locale.setlocale(locale.LC_ALL, 'en_US.UTF-8') # UTF-8 for ncurses
        
    def register_cb(self, name, cb, args=[]):
        """Registers callback
           Name:        Event:
           key_pressed  when key is pressed
        """
        self.callback[name] = cb
        self.callback_args[name] = args

    def call_cb(self, name, extra_args=[]):
        args = extra_args + self.callback_args[name]
        return self.callback[name](*args)

    def display(self):
        """Displays curses based CUI
        """
        try:
            self.enable_curses()
            (self.display_height, self.display_width) = self.stdscr.getmaxyx()                
            self.setup_curses()
            while True:
                self._print_cui()
                if self._wait_for_user():
                    break
                
        except KeyboardInterrupt: # CTRL+C when CUI is visible
            pass
        finally:
            self.disable_curses()

    def enable_curses(self):
        """Enables curses library to display CUI.
           This code is based on curses.wrapper code
        """
        self.stdscr = curses.initscr()
        curses.noecho()
        curses.cbreak()
        self.stdscr.keypad(1)
        try:
            curses.start_color()
        except:
            pass

        self.setup_curses()

    def disable_curses(self):
        """Cleans up after curses, so returning to the console is save.
           This code is based on curses.wrapper code
        """
        self.stdscr.keypad(0)
        curses.echo()
        curses.nocbreak()
        curses.endwin()

    def setup_curses(self):
        """Does application specyfic configuration of curses
        """
        curses.curs_set(0)

    def _wait_for_user(self):
        """Interacts with the user when CUI is displayed
        """
        
        key = self.stdscr.getkey()
        
        if self.selection != None:
            if key == 'KEY_UP':
                if self.selection > 0:
                    self.selection = self.selection - 1            
                if self.selection - self.scroll < 0:
                    self.scroll = self.selection
            elif key == 'KEY_DOWN':
                if self.selection < len(self.items) - 1:
                    self.selection = self.selection + 1
                if self.selection - self.scroll >= self.display_height - len(self.header):
                    self.scroll = len(self.header) + self.selection - self.display_height + 1
            if key == 'KEY_PPAGE':
                self.selection = self.selection - self.page_size
                if self.selection < 0: self.selection = 0
                if self.selection - self.scroll < 0:
                    self.scroll = self.selection
            if key == 'KEY_NPAGE':
                self.selection = self.selection + self.page_size
                if self.selection > len(self.items) - 1:
                    self.selection = len(self.items) - 1                    
                if self.selection - self.scroll >= self.display_height - len(self.header):
                    self.scroll = len(self.header) + self.selection - self.display_height + 1

            return self.call_cb('key_pressed', [key])

    def _print_item(self, position, selected, header=False):
        """Prints single line of the CUI
        """
        x = 0
        y = position
        from_y = 0
        if header:            
            item = self.header[position]
        else:
            display_y_offset = len(self.header)
            y += display_y_offset - self.scroll
            item = self.items[position]
            from_y = max(0, display_y_offset)
        
        #text = str(item)#.encode('utf8').replace('\n', ' ')
        text = item.encode('utf8').replace('\n', ' ')

        if (y >= from_y) and (y < self.display_height):

            w = self.display_width-1 # self.stdscr.addstr sometimes raise an error when full width used
            if len(text) > w:
                text = (text[0:max(w-3,0)] + '...')[0:w]

            if selected and not header:
                self.stdscr.attron(curses.A_STANDOUT) # Highlighting ON

            if hasattr(item, 'bold'):
                if item.bold:
                    self.stdscr.attron(curses.A_BOLD) # Bold ON            

            try:            
                self.stdscr.addstr(y, x, text)
            except curses.error, e:
                raise PrintingError(e, y, x, text)

            self.stdscr.attroff(curses.A_STANDOUT)    # Highlighting OFF
            self.stdscr.attroff(curses.A_BOLD)        # Bold OFF

    def _print_cui(self):
        """Prints whole CUI
        """

        self.stdscr.clear()

        # Print header
        for position in range(len(self.header)):
            self._print_item(position, position==self.selection, True)

        # Print regular lines
        for position in range(len(self.items)):
            self._print_item(position, position==self.selection)

        self.stdscr.refresh()

class Bold(unicode):
    """ Embedds text that should be displayed in bold
    """
    bold = 1
