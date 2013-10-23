#!/usr/bin/env python

from distutils.core import setup

setup(name='cvifier',
      version='0.1dev',
      description='Python Distribution Utilities',
      author='Erik Tollerud',
      author_email='erik.tollerud@gmail.com',
      url='https://github.com/eteq/cvifier',
      packages=['cvifier'],
      provides='cvifier',
      requires=['requests']
     )