#!/usr/bin/python3

"""Libvirt port-forwarding hook.

Libvirt hook for setting up iptables port-forwarding rules when using NAT-ed
networking on a host with a single public IP address.

Original version by "Sascha Peilicke <saschpe@gmx.de>" adapted for my use-case.

"""

__author__ = "Martin Bo Kristensen Groenholdt <martin.groenholdt@gmail.com>"
__version__ = "0.2.0"

import os
import subprocess
import sys
import syslog
from importlib.machinery import SourceFileLoader

# Path to the forwarding configuration file
CONFIG_PATH = os.getenv('CONFIG_PATH') or os.path.dirname(
    os.path.abspath(__file__))
CONFIG_FILENAME = os.getenv('CONFIG_FILENAME') or os.path.join(CONFIG_PATH,
                                                               'fwdconf.py')
IPTABLES_BINARY = os.getenv('IPTABLES_BINARY') or subprocess.check_output(
    ['which', 'iptables']).strip().decode('ascii')


def logged_call(args):
    """
    Log command and stdout from external call.
    """
    if config.DEBUG:
        syslog.syslog(' '.join(args))

    ret = subprocess.Popen(args,stdout=subprocess.PIPE)
    ret = ret.communicate()[0].decode('ascii')
    if ret != '':
        syslog.syslog(ret)


def ctrl_network(action, libvirt_object, config):
    network = None
    if libvirt_object in config.NETWORKS.keys():
        network = config.NETWORKS[libvirt_object]
    else:
        syslog.syslog('No network configuration, terminating.')
        exit(0)

    if action in ['unplugged']:
        syslog.syslog('Removing forwarding rule for network ' +
                      '{}'.format(network))
        logged_call(
            [IPTABLES_BINARY, '-D', 'FORWARD', '-m', 'state', '-d',
             network, '--state', 'NEW,RELATED,ESTABLISHED', '-j',
             'ACCEPT'])

    if action in ['plugged']:
        syslog.syslog('Adding forwarding rule for network ' +
                      '{}'.format(network))
        logged_call(
            [IPTABLES_BINARY, '-I', 'FORWARD', '-m', 'state', '-d',
             network, '--state', 'NEW,RELATED,ESTABLISHED', '-j',
             'ACCEPT'])


def ctrl_machine(action, libvirt_object, config):
    machine = {}
    if libvirt_object in config.MACHINES.keys():
        machine = config.MACHINES[libvirt_object]
    else:
        syslog.syslog('No forwarding configuration, terminating.')
        exit(0)

    if action in ['stopped', 'reconnect']:
        for ports in machine['port_map']:
            public_port = ports[0]
            private_port = ports[1]

            syslog.syslog('Setting up machine "{}"'.format(machine))
            syslog.syslog('Private IP and port ' +
                          '{}:{}'.format(machine['private_ip'],
                                         private_port))
            syslog.syslog('Public IP and port ' +
                          '{}:{}'.format(config.PUBLIC_IP,
                                         public_port))
            logged_call(
                [IPTABLES_BINARY, '-t', 'nat', '-D', 'PREROUTING', '-p',
                 'tcp', '-d', config.PUBLIC_IP, '--dport',
                 public_port, '-j',
                 'DNAT', '--to-destination',
                 '{0}:{1}'.format(machine['private_ip'],
                                  private_port)])

    if action in ['start', 'reconnect']:
        for ports in machine['port_map']:
            public_port = ports[0]
            private_port = ports[1]

            syslog.syslog('Private IP and port ' +
                          '{}:{}'.format(machine['private_ip'],
                                         private_port))
            syslog.syslog('Public IP and port ' +
                          '{}:{}'.format(config.PUBLIC_IP,
                                         public_port))
            logged_call(
                [IPTABLES_BINARY, '-t', 'nat', '-I', 'PREROUTING', '-p',
                 'tcp', '-d', config.PUBLIC_IP, '--dport',
                 public_port, '-j',
                 'DNAT', '--to-destination',
                 '{0}:{1}'.format(machine['private_ip'],
                                  private_port)])


if __name__ == '__main__':
    hook, libvirt_object, action = sys.argv[0:3]
    hook = os.path.basename(hook)
    syslog.syslog('{} {} for {}'.format(action, hook, libvirt_object))

    try:
        # Import config.py
        config = SourceFileLoader('config', CONFIG_FILENAME).load_module()
        machine = dict()
        network = dict()

        if hook in ['qemu', 'lxc']:
            ctrl_machine(action, libvirt_object, config)

        if hook == 'network':
            ctrl_network(action, libvirt_object, config)

    except FileNotFoundError:
        syslog.syslog('No fwdconf.py.py found, terminating.')
        exit(0)
    except SyntaxError as exception:
        syslog.syslog('Syntax error in fwdconf.py.py configuration file.')
        syslog.syslog(str(exception.lineno) + ':' + str(exception.offset) +
                      ': ' + exception.text)
        exit(1)
