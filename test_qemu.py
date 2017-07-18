#!/usr/bin/python3

import imp
import unittest
from importlib.machinery import SourceFileLoader

qemu = SourceFileLoader('hooks.py', 'hooks.py').load_module()


class QemuTestCase(unittest.TestCase):
    config = None

    def __init__(self, *args, **kwargs):
        super(QemuTestCase, self).__init__(*args, **kwargs)
        try:
            self.config = qemu.read_config(qemu.CONFIG_FILENAME)
        except FileNotFoundError:
            print('No config.py.py found, terminating.')
        except SyntaxError as exception:
            print('Syntax error in config.py.py configuration file.')
            print(str(exception.lineno) + ':' + str(exception.offset) +
                  ': ' + exception.text)


    def test_config(self):
        self.assertEqual(self.config.DEBUG, False)
        self.assertEqual(self.config.MACHINES, {
            'test': {
                'private_ip': '192.168.122.2',
                'port_map': [['2222', '22'], ['8002', '80']]
            }
        })
        self.assertEqual(self.config.NETWORKS, {
            'default': '192.168.122.0/24'
        })
        self.assertEqual(self.config.PUBLIC_IP, '192.168.0.166')


    def test_network_plugged(self):
        cmd = qemu.ctrl_network('plugged', 'default', self.config)
        self.assertEqual(cmd, [
            qemu.IPTABLES_BINARY + ' -I FORWARD -m state -d 192.168.122.0/24 --state NEW,RELATED,ESTABLISHED -j ACCEPT'])

    def test_network_unplugged(self):
        cmd = qemu.ctrl_network('unplugged', 'default', self.config)
        self.assertEqual(cmd, [
            qemu.IPTABLES_BINARY + ' -D FORWARD -m state -d 192.168.122.0/24 --state NEW,RELATED,ESTABLISHED -j ACCEPT'])

    def test_machine_start(self):
        cmd = qemu.ctrl_machine('start', 'test', self.config)
        pass

    def test_machine_stopped(self):
        cmd = qemu.ctrl_machine('stopped', 'test', self.config)
        pass

    def test_reconnect(self):
        cmd = qemu.ctrl_machine('reconnect', 'test', self.config)
        pass
