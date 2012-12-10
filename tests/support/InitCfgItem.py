#!/usr/bin/python
"""
Initializer Configuration Item
"""

__author__ = "Lee Duncan <leeman.duncan@gmail.com>"


class InitCfgItem:
    def __init__(self, iface_name, dev, key=None):
        self.iface_name = iface_name
        self.dev = dev
        self.key = key
