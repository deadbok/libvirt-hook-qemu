#!/usr/bin/python3
"""
Libvirt port-forwarding hook control utility unit tests.

0.0.1:
======

"""

import argparse
import json
import imp
import unittest
from hookctrl import str2bool, create_argparser, check_args, add_machine, \
    remove_machine, add_network, remove_network, add_port, remove_port, \
    process_config, ConfigError


class HookCTRLTestCase(unittest.TestCase):
    config = None

    def __init__(self, *args, **kwargs):
        super(HookCTRLTestCase, self).__init__(*args, **kwargs)

    def base_config(self):
        return {
            'debug': False,
            'machines': {},
            'networks': {},
            'public_ip': ''
        }

    def test_str2bool(self):
        # Test conversion of true values to True
        self.assertEqual(str2bool('true'), True)
        self.assertEqual(str2bool('True'), True)
        self.assertEqual(str2bool('t'), True)
        self.assertEqual(str2bool('yes'), True)
        self.assertEqual(str2bool('y'), True)
        self.assertEqual(str2bool('1'), True)

        # Test conversion of false values to False
        self.assertEqual(str2bool('false'), False)
        self.assertEqual(str2bool('False'), False)
        self.assertEqual(str2bool('f'), False)
        self.assertEqual(str2bool('no'), False)
        self.assertEqual(str2bool('n'), False)
        self.assertEqual(str2bool('0'), False)

        # Test failed conversion of true values to False
        self.assertNotEqual(str2bool('true'), False)
        self.assertNotEqual(str2bool('True'), False)
        self.assertNotEqual(str2bool('t'), False)
        self.assertNotEqual(str2bool('yes'), False)
        self.assertNotEqual(str2bool('y'), False)
        self.assertNotEqual(str2bool('1'), False)

        # Test failed conversion of false values to True
        self.assertNotEqual(str2bool('false'), True)
        self.assertNotEqual(str2bool('False'), True)
        self.assertNotEqual(str2bool('f'), True)
        self.assertNotEqual(str2bool('no'), True)
        self.assertNotEqual(str2bool('n'), True)
        self.assertNotEqual(str2bool('0'), True)

    def test_create_argparser(self):
        arg_parser = create_argparser()
        self.assertIsInstance(arg_parser, argparse.ArgumentParser)

    def test_check_args(self):
        arg_parser = create_argparser()

        # Add machine
        args = arg_parser.parse_args(['--cmd', 'add_machine'])
        with self.assertRaises(argparse.ArgumentTypeError):
            check_args(args)

        args = arg_parser.parse_args(
            ['--cmd', 'add_machine', '--name', 'test'])
        with self.assertRaises(argparse.ArgumentTypeError):
            check_args(args)

        args = arg_parser.parse_args(
            ['--cmd', 'add_machine', '--name', 'test', '--private_ip', 'a.b.c.d'])
        with self.assertRaises(argparse.ArgumentTypeError):
            check_args(args)

        args = arg_parser.parse_args(
            ['--cmd', 'add_machine', '--name', 'test', '--private_ip', '999.888.777.666'])
        with self.assertRaises(argparse.ArgumentTypeError):
            check_args(args)

        args = arg_parser.parse_args(
            ['--cmd', 'add_machine', '--name', 'test', '--private_ip', ''])
        with self.assertRaises(argparse.ArgumentTypeError):
            check_args(args)

        args = arg_parser.parse_args(
            ['--cmd', 'add_machine', '--name', 'test', '--private_ip', '192.168.122.6'])
        self.assertEqual(check_args(args), True)

        # Add network
        args = arg_parser.parse_args(['--cmd', 'add_network'])
        with self.assertRaises(argparse.ArgumentTypeError):
            check_args(args)

        args = arg_parser.parse_args(
            ['--cmd', 'add_network', '--name', 'test'])
        with self.assertRaises(argparse.ArgumentTypeError):
            check_args(args)

        args = arg_parser.parse_args(
            ['--cmd', 'add_network', '--name', 'test', '--network', 'a.b.c.d'])
        with self.assertRaises(argparse.ArgumentTypeError):
            check_args(args)

        args = arg_parser.parse_args(
            ['--cmd', 'add_network', '--name', 'test', '--network', '999.888.777.666/555'])
        with self.assertRaises(argparse.ArgumentTypeError):
            check_args(args)

        args = arg_parser.parse_args(
            ['--cmd', 'add_network', '--name', 'test', '--network', ''])
        with self.assertRaises(argparse.ArgumentTypeError):
            check_args(args)

        args = arg_parser.parse_args(
            ['--cmd', 'add_network', '--name', 'test', '--network', '192.168.122.0/24'])
        self.assertEqual(check_args(args), True)

        # Add port
        args = arg_parser.parse_args(['--cmd', 'add_port'])
        with self.assertRaises(argparse.ArgumentTypeError):
            check_args(args)

        with self.assertRaises((argparse.ArgumentError, SystemExit)):
            arg_parser.parse_args(['--cmd', 'add_port', '--public_port'])

        with self.assertRaises((argparse.ArgumentError, SystemExit)):
            arg_parser.parse_args(['--cmd', 'add_port', '--vm-port'])

        args = arg_parser.parse_args(
            ['--cmd', 'add_port', '--public_port', '8080'])
        with self.assertRaises(argparse.ArgumentTypeError):
            check_args(args)

        args = arg_parser.parse_args(['--cmd', 'add_port', '--vm-port', '80'])
        with self.assertRaises(argparse.ArgumentTypeError):
            check_args(args)

        args = arg_parser.parse_args(
            ['--cmd', 'add_port', '--public_port', '-1', '--vm-port', '80'])
        with self.assertRaises(argparse.ArgumentTypeError):
            check_args(args)

        args = arg_parser.parse_args(
            ['--cmd', 'add_port', '--public_port', '8080', '--vm-port', '-1'])
        with self.assertRaises(argparse.ArgumentTypeError):
            check_args(args)

        args = arg_parser.parse_args(
            ['--cmd', 'add_port', '--public_port', '66000', '--vm-port', '80'])
        with self.assertRaises(argparse.ArgumentTypeError):
            check_args(args)

        args = arg_parser.parse_args(
            ['--cmd', 'add_port', '--public_port', '8080', '--vm-port', '66000'])
        with self.assertRaises(argparse.ArgumentTypeError):
            check_args(args)

        args = arg_parser.parse_args(
            ['--cmd', 'add_port', '--public_port', '8080', '--vm-port', '80'])
        self.assertEqual(check_args(args), True)

        # remove port
        args = arg_parser.parse_args(['--cmd', 'remove_port'])
        with self.assertRaises(argparse.ArgumentTypeError):
            check_args(args)

        with self.assertRaises((argparse.ArgumentError, SystemExit)):
            arg_parser.parse_args(['--cmd', 'remove_port', '--public_port'])

        with self.assertRaises((argparse.ArgumentError, SystemExit)):
            arg_parser.parse_args(['--cmd', 'remove_port', '--vm-port'])

        args = arg_parser.parse_args(
            ['--cmd', 'remove_port', '--public_port', '8080'])
        with self.assertRaises(argparse.ArgumentTypeError):
            check_args(args)

        args = arg_parser.parse_args(
            ['--cmd', 'remove_port', '--vm-port', '80'])
        with self.assertRaises(argparse.ArgumentTypeError):
            check_args(args)

        args = arg_parser.parse_args(
            ['--cmd', 'remove_port', '--public_port', '-1', '--vm-port', '80'])
        with self.assertRaises(argparse.ArgumentTypeError):
            check_args(args)

        args = arg_parser.parse_args(
            ['--cmd', 'remove_port', '--public_port', '8080', '--vm-port', '-1'])
        with self.assertRaises(argparse.ArgumentTypeError):
            check_args(args)

        args = arg_parser.parse_args(
            ['--cmd', 'add_port', '--public_port', '66000', '--vm-port', '80'])
        with self.assertRaises(argparse.ArgumentTypeError):
            check_args(args)

        args = arg_parser.parse_args(
            ['--cmd', 'add_port', '--public_port', '8080', '--vm-port', '66000'])
        with self.assertRaises(argparse.ArgumentTypeError):
            check_args(args)

        args = arg_parser.parse_args(
            ['--cmd', 'add_port', '--public_port', '8080', '--vm-port', '80'])
        self.assertEqual(check_args(args), True)

    def test_add_machine(self):
        # Add a machine an test if it's there
        config = add_machine(self.base_config(), 'test', '1.1.1.1')
        self.assertDictEqual(
            {'test': {'private_ip': '1.1.1.1', 'port_map': []}},
            config['machines'])

    def test_remove_machine(self):
        # Add machine, check its presence, remove it and check that it's gone.
        config = add_machine(self.base_config(), 'test', '1.1.1.1')
        self.assertIn('test', config['machines'].keys())
        config = remove_machine(config, 'test')
        self.assertNotIn('test', config['machines'].keys())

    def add_network(self):
        # Add a network an test if it's there
        config = add_network(self.base_config(), 'test', '1.1.1.1/32')
        self.assertDictEqual(
            {'test': '1.1.1.1/32'},
            config['networks'])

    def test_remove_network(self):
        # Add network, check its presence, remove it and check that it's gone.
        config = add_network(self.base_config(), 'test', '1.1.1.1/32')
        self.assertIn('test', config['networks'].keys())
        config = remove_network(config, 'test')
        self.assertNotIn('test', config['networks'].keys())

    def test_add_port(self):
        # Add a machine an test if it's there
        config = add_machine(self.base_config(), 'test', '1.1.1.1')
        self.assertDictEqual(
            {'test': {'private_ip': '1.1.1.1', 'port_map': []}},
            config['machines'])
        # Add a port mapping an test if it's there
        config = add_port(config, 'test', 8080, 80)
        self.assertListEqual([8080, 80],
                             config['machines']['test']['port_map'][0])

    def test_remove_port(self):
        # Add a machine an test if it's there
        config = add_machine(self.base_config(), 'test', '1.1.1.1')
        self.assertDictEqual(
            {'test': {'private_ip': '1.1.1.1', 'port_map': []}},
            config['machines'])
        # Add a port mapping and test if it's there
        config = add_port(config, 'test', 8080, 80)
        self.assertListEqual([8080, 80],
                             config['machines']['test']['port_map'][0])
        # Remove a port mapping and test if it's gone
        config = remove_port(config, 'test', 8080, 80)
        self.assertNotIn([8080, 80],
                         config['machines']['test']['port_map'])

    def test_process_config(self):
        # Test simple operations
        config = process_config(self.base_config(),
                                args=type('config',
                                          (object,),
                                          {
                                              'debug': True,
                                              'public_ip': '1.1.1.1'
                                          }
                                          )
                                )
        self.assertEqual(config['debug'], True)
        self.assertEqual(config['public_ip'], '1.1.1.1')

        # Test adding machine
        config = process_config(self.base_config(),
                                args=type('config',
                                          (object,),
                                          {
                                              'cmd': 'add_machine',
                                              'name': 'test',
                                              'private_ip': '1.1.1.1'
                                          }
                                          )
                                )
        self.assertDictEqual(
            {'test': {'private_ip': '1.1.1.1', 'port_map': []}},
            config['machines'])

        # Adding again should cause an exception
        with self.assertRaises(ConfigError):
            process_config(config,
                           args=type('config',
                                     (object,),
                                     {
                                         'cmd': 'add_machine',
                                         'name': 'test',
                                         'private_ip': '1.1.1.1'
                                     }
                                     )
                           )

        # Test removing machine
        config = process_config(config,
                                args=type('config',
                                          (object,),
                                          {
                                              'cmd': 'remove_machine',
                                              'name': 'test'
                                          }
                                          )
                                )
        self.assertNotIn('test', config['machines'].keys())

        # Test adding network
        config = process_config(self.base_config(),
                                args=type('config',
                                          (object,),
                                          {
                                              'cmd': 'add_network',
                                              'name': 'test',
                                              'network': '1.1.1.1/32'
                                          }
                                          )
                                )
        self.assertDictEqual(
            {'test': '1.1.1.1/32'},
            config['networks'])

        # Adding again should cause an exception
        with self.assertRaises(ConfigError):
            process_config(config,
                           args=type('config',
                                     (object,),
                                     {
                                         'cmd': 'add_network',
                                         'name': 'test',
                                                'network': '1.1.1.1/32'
                                     }
                                     )
                           )

        # Test removing network
        config = process_config(config,
                                args=type('config',
                                          (object,),
                                          {
                                              'cmd': 'remove_network',
                                              'name': 'test'
                                          }
                                          )
                                )
        self.assertNotIn('test', config['networks'].keys())

        # Test adding port mapping to a non-existing machine
        with self.assertRaises(ConfigError):
            process_config(config,
                           args=type('config',
                                     (object,),
                                     {
                                         'cmd': 'add_port',
                                         'name': 'test',
                                         'public_port': 8080,
                                         'vm_port': 80
                                     }
                                     )
                           )

        # Test adding a port mapping
        config = process_config(self.base_config(),
                                args=type('config',
                                          (object,),
                                          {
                                              'cmd': 'add_machine',
                                              'name': 'test',
                                              'private_ip': '1.1.1.1'
                                          }
                                          )
                                )
        self.assertDictEqual(
            {'test': {'private_ip': '1.1.1.1', 'port_map': []}},
            config['machines'])

        # Add a port mapping
        config = process_config(config,
                                args=type('config',
                                          (object,),
                                          {
                                              'cmd': 'add_port',
                                              'name': 'test',
                                              'public_port': 8080,
                                              'vm_port': 80
                                          }
                                          )
                                )
        self.assertListEqual([8080, 80],
                             config['machines']['test']['port_map'][0])

        # Adding again should cause an exception
        with self.assertRaises(ConfigError):
            process_config(config,
                           args=type('config',
                                     (object,),
                                     {
                                         'cmd': 'add_port',
                                         'name': 'test',
                                         'public_port': 8080,
                                         'vm_port': 80
                                     }
                                     )
                           )
        # Test removing non-existing port mapping
        with self.assertRaises(ConfigError):
            process_config(config,
                                args=type('config',
                                          (object,),
                                          {
                                              'cmd': 'remove_port',
                                              'name': 'test',
                                              'public_port': 808,
                                              'vm_port': 80
                                          }
                                          )
                                )

        # Test removing port
        config = process_config(config,
                                args=type('config',
                                          (object,),
                                          {
                                              'cmd': 'remove_port',
                                              'name': 'test',
                                              'public_port': 8080,
                                              'vm_port': 80
                                          }
                                          )
                                )
        self.assertListEqual([], config['machines']['test']['port_map'])


if __name__ == '__main__':
    unittest.main()
