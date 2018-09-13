#!/usr/bin/python3

"""Libvirt port-forwarding hook control utility.

Utility for adding, modifying and deleting machine definitions from the Libvirt 
hook configuration file.

0.0.1:
======


"""

__author__ = "Martin Bo Kristensen Groenholdt <martin.groenholdt@gmail.com>"
__version__ = "0.0.1"

import argparse
import json
import os
import sys
from hookjsonconf import HookConfig

CONFIG_PATH = os.getenv('CONFIG_PATH') or os.path.dirname(
    os.path.abspath(__file__))
# Name of the forwarding configuration file.
CONFIG_FILENAME = os.getenv('CONFIG_FILENAME') or os.path.join(CONFIG_PATH,
                                                               'config.json')

def str2bool(v):
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')


def parse_cmd_line(help=False):
    """
    Parse the command line arguments
    """
    arg_parser = argparse.ArgumentParser(description='Utility for adding, ' +
                                         'modifying and deleting machine ' +
                                         'definitions from the libvirt hook ' +
                                         'configuration file.')
    # Simple global configuration entries
    arg_parser.add_argument("--debug", type=str2bool, default=argparse.SUPPRESS,
                            help="Enable debugging when the hook is executed."
                            )
    arg_parser.add_argument("--public_ip", type=str, default=argparse.SUPPRESS,
                            help="Public IP address of the libvirt host."
                            )
    # Adding and removing sub configuration entries
    arg_parser.add_argument("--cmd", choices=['add_machine',
                                              'del_machine',
                                              'add_network',
                                              'del_network',
                                              'add_port',
                                              'del_port'], type=str, default='',
                            help="Sub entry commands.")
    # Sub entry values
    arg_parser.add_argument("--name", type=str, default='',
                            help="Name of the entry.")
    arg_parser.add_argument("--private_ip", type=str,
                            help="Set the private IP address of a machine.")
    arg_parser.add_argument("--public_port", type=int,
                            help="Set the public port of the mapping.")
    arg_parser.add_argument("--vm-port", type=int,
                            help="Set the machine port of the mapping.")
    arg_parser.add_argument("--network", type=str,
                            help="Set IP range of a network.")

    args = arg_parser.parse_args()

    # Check that the command has a name parameter
    if args.cmd != '':
        if args.name == '':
            arg_parser.print_usage()
            print('hookctrl.py: error: argument --cmd ' + args.cmd + ' needs the --name argument')
            exit(1)
    if help:
        arg_parser.print_help()
        exit(1)

    return args


def add_machine():
    pass


def remove_machine(name=''):
    pass


def process_config(config, args=None):
    if args.cmd != '':
        if args.cmd == 'add_machine':
            print('Adding machine: {}'.format(args.name))
        elif args.cmd == 'del_machine':
            print('Removing machine: {}'.format(args.name))
        elif args.cmd == 'add_network':
            print('Adding network: {}'.format(args.name))
        elif args.cmd == 'del_network':
            print('Removing network: {}'.format(args.name))
        elif args.cmd == 'add_port':
            print('Adding port: {}'.format(args.name))
        elif args.cmd == 'del_port':
            print('Removing port: {}'.format(args.name))

    if 'debug' in args:
        config['debug'] = args.debug

    if 'public_ip' in args:
        config['public_ip'] = args.public_ip

    ret = config

    return config


def main():
    config = None

    if (len(sys.argv) < 2):
        parse_cmd_line(True)
        exit(1)
    else:
        args = parse_cmd_line()
    try:
        json_config = HookConfig()
        # Path to the forwarding configuration file
        with open(CONFIG_FILENAME, 'r') as json_config_file:
            json_config = HookConfig(json_config_file.read())
            config = json_config.config

        config = process_config(config, args)

        print(json_config.build(config, True))
    except FileNotFoundError:
        print('No config.json found, terminating.')
    except json.JSONDecodeError as jde:
        print('Error loading configuration file: {} in {} line {} char {}'.format(
            jde.msg, jde.doc, jde.lineno, jde.colno))


if __name__ == '__main__':
    main()
    exit(0)
