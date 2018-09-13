#!/usr/bin/python3

import json
import imp
import unittest
from hookjsonconf import HookConfig
from hooks import CONFIG_PATH, CONFIG_FILENAME, IPTABLES_BINARY, ctrl_network, ctrl_machine

class QemuTestCase(unittest.TestCase):
    config = None

    def __init__(self, *args, **kwargs):
        super(QemuTestCase, self).__init__(*args, **kwargs)
        self.config = None
        try:
            # Import configuration
            json_config = HookConfig()

            with open(CONFIG_FILENAME, 'r') as json_config_file:
                json_config = HookConfig(json_config_file.read())
                self.config = json_config.config
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

    def test_network_plugged(self):
        cmd = ctrl_network('plugged', 'default', self.config)
        self.assertEqual(cmd, [
            IPTABLES_BINARY + ' -I FORWARD -m state -d 192.168.122.0/24 --state NEW,RELATED,ESTABLISHED -j ACCEPT'])

    def test_network_unplugged(self):
        cmd = ctrl_network('unplugged', 'default', self.config)
        self.assertEqual(cmd, [
            IPTABLES_BINARY + ' -D FORWARD -m state -d 192.168.122.0/24 --state NEW,RELATED,ESTABLISHED -j ACCEPT'])

    def test_machine_start(self):
        cmd = ctrl_machine('start', 'test', self.config)
        pass

    def test_machine_stopped(self):
        cmd = ctrl_machine('stopped', 'test', self.config)
        pass

    def test_reconnect(self):
        cmd = ctrl_machine('reconnect', 'test', self.config)
        pass
