#!/usr/bin/env python
# -*- coding: utf-8 -*-

#Author: Grzegorz Krason
#webpage: http://krason.biz/#frss

from textwrap import fill
import subprocess

def pager(text, width=0):
    """Wraps the text according to the width of the screen. Then displays the
       text using 'less' command
    """
    # 'fill' function used below preserves the words (dont't break them at the
    # end of the line). \n would be replaced by spaces, so we have to prevent
    # this. Control sequences are considered to be words.
    if width:
        lines = text.split('\n')
        lines = [fill(line, width) for line in lines]
        text = '\n'.join(lines)

    # -R allows to use control sequences (colorful syntax)
    # ncurses is assumed to be disabled, otherwise arrow keys stop working
    # after returning to ncurses
    proc = subprocess.Popen(['less', '-R'], stdin=subprocess.PIPE)
    proc.stdin.write(text)
    proc.stdin.close()
    proc.wait()
