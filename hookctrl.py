#!/usr/bin/python3

"""Libvirt port-forwarding hook control utility.

Utility for adding, modifying and deleting machine definitions from the Libvirt 
hook configuration file.

0.0.1:
======
 * Initial version

"""

__author__ = "Martin Bo Kristensen Groenholdt <martin.groenholdt@gmail.com>"
__version__ = "0.0.1"

import argparse
import ipaddress
import json
import os
import sys
from enum import Enum
from hookjsonconf import HookConfig

CONFIG_PATH = os.getenv('CONFIG_PATH') or os.path.dirname(
    os.path.abspath(__file__))
# Name of the forwarding configuration file.
CONFIG_FILENAME = os.getenv('CONFIG_FILENAME') or os.path.join(CONFIG_PATH,
                                                               'config.json')


class ConfigError(Exception):
    pass

# class ArgumentParser(argparse.ArgumentParser):
#     """
#     Derived class preventing exit on parser error
#     """
#     def error(self, message):
#         exc = sys.exc_info()[1]
#         if exc:
#             raise exc


def str2bool(v):
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')


def create_argparser():
    """
    Parse the command line arguments
    """
    arg_parser = argparse.ArgumentParser(description='Utility for adding, ' +
                                         'modifying and deleting machine ' +
                                         'definitions from the libvirt hook ' +
                                         'configuration file.')
    # Simple global configuration entries
    arg_parser.add_argument("--debug", type=str2bool, default=argparse.SUPPRESS,
                            help="Enable debugging when the hook is executed.")
    arg_parser.add_argument("--public_ip", type=str, default=argparse.SUPPRESS,
                            help="Public IP address of the libvirt host.")
    # Adding and removing sub configuration entries
    arg_parser.add_argument("--cmd", choices=['add_machine',
                                              'remove_machine',
                                              'add_network',
                                              'remove_network',
                                              'add_port',
                                              'remove_port'], type=str, default='',
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

    return arg_parser


def check_args(args):
    # Check that the command has a name parameter
    if args.cmd != '':
        if args.cmd not in ['add_machine',
                            'remove_machine',
                            'add_network',
                            'remove_network',
                            'add_port',
                            'remove_port']:
            raise argparse.ArgumentTypeError('wrong command "' + args.cmd + '"')
        if 'port' not in args.cmd:
            if args.name == '':
                raise argparse.ArgumentTypeError('argument --cmd ' + args.cmd +
                                                 ' needs the --name argument')
        if args.cmd == 'add_machine':
            try:
                args.private_ip = ipaddress.ip_address(
                    args.private_ip).exploded
            except ValueError:
                raise argparse.ArgumentTypeError('Invalid private IP address')
        elif args.cmd == 'add_network':
            try:
                args.network = ipaddress.ip_network(
                    args.network).exploded
            except ValueError:
                raise argparse.ArgumentTypeError('Invalid network IP range')
        elif args.cmd == 'add_port' or args.cmd == 'remove_port':
            try:
                args.public_port = int(args.public_port)
            except TypeError:
                raise argparse.ArgumentTypeError('Invalid public port')

            if args.public_port < 0 or args.public_port > 65535:
                raise argparse.ArgumentTypeError('Invalid public port')

            try:
                args.vm_port = int(args.vm_port)
            except TypeError:
                raise argparse.ArgumentTypeError('Invalid vm port')

            if args.vm_port < 0 or args.vm_port > 65535:
                raise argparse.ArgumentTypeError('Invalid vm port')

    return True


def add_machine(config, name, private_ip):
    config['machines'][name] = {}
    config['machines'][name]['private_ip'] = private_ip
    config['machines'][name]['port_map'] = []

    return config


def remove_machine(config, name):
    del config['machines'][name]

    return config


def add_network(config, name, network):
    config['networks'][name] = network

    return config


def remove_network(config, name):
    del config['networks'][name]

    return config


def add_port(config, name, public_port, vm_port):
    config['machines'][name]['port_map'].append([public_port, vm_port])

    return config


def remove_port(config, name, public_port, vm_port):
    port_map = config['machines'][name]['port_map']

    i = 0
    index = -1
    for mapping in port_map:
        if mapping[0] == public_port and mapping[1] == vm_port:
            index = i
            break
        i += 1

    if index != -1:
        del config['machines'][name]['port_map'][index]

    return config


def process_config(config, args=None):
    if 'cmd' in args.__dict__.keys():
        if args.cmd != '':
            if args.cmd == 'add_machine':
                if args.name in config['machines'].keys():
                    raise ConfigError('Machine exists')
                config = add_machine(config, args.name, args.private_ip)
            elif args.cmd == 'remove_machine':
                if args.name not in config['machines'].keys():
                    raise ConfigError('Machine does not exist')
                config = remove_machine(config, args.name)
            elif args.cmd == 'add_network':
                if args.name in config['networks'].keys():
                    raise ConfigError('Network exists')
                config = add_network(config, args.name, args.network)
            elif args.cmd == 'remove_network':
                if args.name not in config['networks'].keys():
                    raise ConfigError('Network does not exist')
                config = remove_network(config, args.name)
            elif args.cmd == 'add_port':
                if args.name not in config['machines'].keys():
                    raise ConfigError('Machine does not exist')
                if [args.public_port, args.vm_port] in config['machines'][args.name]['port_map']:
                    raise ConfigError('Port mapping exists')
                config = add_port(config, args.name, args.public_port, args.vm_port)
            elif args.cmd == 'remove_port':
                if args.name not in config['machines'].keys():
                    raise ConfigError('Machine does not exist')
                if [args.public_port, args.vm_port] not in config['machines'][args.name]['port_map']:
                    raise ConfigError('Port mapping does not exists')
                config = remove_port(config, args.name, args.public_port, args.vm_port)

    if 'debug' in args.__dict__.keys():
        config['debug'] = args.debug

    if 'public_ip' in args.__dict__.keys():
        try:
            config['public_ip'] = ipaddress.ip_address(args.public_ip).exploded
        except ValueError:
            raise argparse.ArgumentTypeError('Invalid public IP address')

    return config


def main():
    config = None
    arg_parser = create_argparser()

    try:
        if (len(sys.argv) < 2):
            arg_parser.print_help()
            exit(1)
        else:
            args = arg_parser.parse_args()

        check_args(args)

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
        print('Error loading configuration file: {} in line {} char {}'.format(
            jde.msg, jde.lineno, jde.colno))
    except argparse.ArgumentTypeError as ate:
        arg_parser.print_usage()
        print(ate)
    except ConfigError as ce:
        print(ce)


if __name__ == '__main__':
    main()
    exit(0)
