#!/usr/bin/env python

from distutils.core import setup

setup(name='frss',
      version='1.0',
      description='RSS Reader',
      author='Grzegorz Krason',
      url='http://krason.biz/#Frss',
      packages=['frsslib'],
      scripts=['usr/bin/frss'],
      )

