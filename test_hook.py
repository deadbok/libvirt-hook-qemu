#!/usr/bin/python3
"""
Libvirt port-forwarding hook unit tests.

0.0.3:
======

 * Uses in source JSON config
 * Mocking of the iptables call
 * Patching of the IPTABLES_BINARY environment variable to avoid sudo.

"""

import json
import imp
import unittest
from unittest import mock
from unittest.mock import patch
from hookjsonconf import HookConfig

with patch.dict('os.environ', values={'IPTABLES_BINARY': 'iptables'}, clear=True):
    from hooks import IPTABLES_BINARY, ctrl_network, ctrl_machine, logged_call


TEST_CONFIG = """
{
    "debug": false,
    "machines": {
        "test": {
            "private_ip": "192.168.122.2",
            "port_map": [
                ["2222", "22"],
                ["8002", "80"]
            ]
        }
    },
    "networks": {
        "default": "192.168.122.0/24"
    },
    "public_ip": "192.168.0.166"
} 
"""


def dummy_func(args, config):
    pass


class QemuTestCase(unittest.TestCase):
    config = None

    def __init__(self, *args, **kwargs):
        super(QemuTestCase, self).__init__(*args, **kwargs)
        self.config = None
        try:
            # Import configuration
            json_config = HookConfig()

            self.config = HookConfig(TEST_CONFIG).config
        except FileNotFoundError:
            print('No config.json found, terminating.')
        except json.JSONDecodeError as jde:
            print('Error loading configuration file: {} in {} line {} char {}'.format(
                jde.msg, jde.doc, jde.lineno, jde.colno))

    def test_config(self):
        self.assertEqual(self.config['debug'], False)
        self.assertEqual(self.config['machines'], {
            'test': {
                'private_ip': '192.168.122.2',
                'port_map': [['2222', '22'], ['8002', '80']]
            }
        })
        self.assertEqual(self.config['networks'], {
            'default': '192.168.122.0/24'
        })
        self.assertEqual(self.config['public_ip'], '192.168.0.166')


    @mock.patch('hooks.logged_call', side_effect=dummy_func)
    def test_network_plugged(self, logged_call_function):
        cmd = ctrl_network('plugged', 'default', self.config)
        self.assertEqual(cmd, [
            IPTABLES_BINARY + ' -I FORWARD -m state -d 192.168.122.0/24 --state NEW,RELATED,ESTABLISHED -j ACCEPT'])


    @mock.patch('hooks.logged_call', side_effect=dummy_func)
    def test_network_unplugged(self, logged_call_function):
        cmd = ctrl_network('unplugged', 'default', self.config)
        self.assertEqual(cmd, [
            IPTABLES_BINARY + ' -D FORWARD -m state -d 192.168.122.0/24 --state NEW,RELATED,ESTABLISHED -j ACCEPT'])

    @mock.patch('hooks.logged_call', side_effect=dummy_func)
    def test_machine_start(self, logged_call_function):
        ctrl_machine('start', 'test', self.config)
        pass


    @mock.patch('hooks.logged_call', side_effect=dummy_func)
    def test_machine_stopped(self, logged_call_function):
        ctrl_machine('stopped', 'test', self.config)
        pass


    @mock.patch('hooks.logged_call', side_effect=dummy_func)
    def test_reconnect(self, logged_call_function):
        ctrl_machine('reconnect', 'test', self.config)
        pass

if __name__ == '__main__':
    unittest.main()
