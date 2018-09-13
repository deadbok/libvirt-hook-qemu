#!/usr/bin/python3

"""Libvirt port-forwarding hook config file parser library.

0.0.1:
======

 * Initial version to decode/encode a JSON configuration

"""

__author__ = "Martin Bo Kristensen Groenholdt <martin.groenholdt@gmail.com>"
__version__ = "0.0.1"

import json


class HookConfig:
    """
    Class for keeping configuration data in JSON strings.
    """

    def __init__(self, config=None):
        """
        Constructor
        """
        if config is not None:
            self.parse(config)
        else:
            self.config = None

    def parse(self, config):
        """
        Parse a JSON string as configuration data
        """
        self.config = json.loads(config)
        return self.config

    def build(self, config, pretty=False):
        """
        Encode configuration data as a JSON string
        """
        jconf = ''
        if pretty:
            jconf = json.dumps(config, indent=4, sort_keys=True)
        else:
            jconf = json.dumps(config)
        return(jconf)
