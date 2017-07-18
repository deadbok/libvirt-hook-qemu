#!/usr/bin/python3

"""Libvirt port-forwarding hook.

Libvirt hook for setting up iptables port-forwarding rules when using NAT-ed
networking on a host with a single public IP address.

Original version by "Sascha Peilicke <saschpe@gmx.de>" adapted for my use-case.

0.2.1:
======

 * Renamed fwdconf to config.py
 * Rewrote unit tests
 * Add log function.

"""

__author__ = "Martin Bo Kristensen Groenholdt <martin.groenholdt@gmail.com>"
__version__ = "0.2.1"

import os
import subprocess
import sys
import syslog
from importlib.machinery import SourceFileLoader

# Path to the forwarding configuration file
CONFIG_PATH = os.getenv('CONFIG_PATH') or os.path.dirname(
    os.path.abspath(__file__))
CONFIG_FILENAME = os.getenv('CONFIG_FILENAME') or os.path.join(CONFIG_PATH,
                                                               'config.py')
IPTABLES_BINARY = os.getenv('IPTABLES_BINARY') or subprocess.check_output(
    ['which', 'iptables']).strip().decode('ascii')


def log(message='', priority=syslog.LOG_INFO):
    syslog.syslog(priority, message)


def logged_call(args, config):
    """
    Log command and stdout from external call.
    """
    if config.DEBUG:
        log(' '.join(args), syslog.LOG_DEBUG)

    ret = subprocess.Popen(args, stdout=subprocess.PIPE)
    ret = ret.communicate()[0].decode('ascii')
    if ret != '':
        log(ret, syslog.LOG_ALERT)


def ctrl_network(action, libvirt_object, config):
    cmds = list()
    network = None
    if libvirt_object in config.NETWORKS.keys():
        network = config.NETWORKS[libvirt_object]
    else:
        log('No network configuration, terminating.')
        exit(0)

    if action in ['unplugged']:
        log('Removing forwarding rule for network ' +
            '{}'.format(network))
        cmd = [IPTABLES_BINARY, '-D', 'FORWARD', '-m', 'state', '-d',
               network, '--state', 'NEW,RELATED,ESTABLISHED', '-j',
               'ACCEPT']
        logged_call(cmd, config)
        cmds.append(' '.join(cmd))

    if action in ['plugged']:
        log('Adding forwarding rule for network ' +
            '{}'.format(network))
        cmd = [IPTABLES_BINARY, '-I', 'FORWARD', '-m', 'state', '-d',
               network, '--state', 'NEW,RELATED,ESTABLISHED', '-j',
               'ACCEPT']
        logged_call(cmd, config)
        cmds.append(' '.join(cmd))

    return (cmds)


def ctrl_machine(action, libvirt_object, config):
    cmds = list()
    machine = {}
    if libvirt_object in config.MACHINES.keys():
        machine = config.MACHINES[libvirt_object]
    else:
        log('No forwarding configuration, terminating.')
        exit(0)

    if action in ['stopped', 'reconnect']:
        log('Remove {} forwarding rules'.format(libvirt_object))
        for ports in machine['port_map']:
            public_port = ports[0]
            private_port = ports[1]
            cmd = [IPTABLES_BINARY, '-t', 'nat', '-D', 'PREROUTING', '-p',
                   'tcp', '-d', config.PUBLIC_IP, '--dport',
                   public_port, '-j',
                   'DNAT', '--to-destination',
                   '{0}:{1}'.format(machine['private_ip'],
                                    private_port)]

            log(' Private IP and port ' +
                '{}:{}'.format(machine['private_ip'],
                               private_port))
            log(' Public IP and port ' +
                '{}:{}'.format(config.PUBLIC_IP,
                               public_port))
            logged_call(cmd, config)
            cmds.append(' '.join(cmd))

    if action in ['start', 'reconnect']:
        log('Insert {} forwarding rules'.format(libvirt_object))
        for ports in machine['port_map']:
            public_port = ports[0]
            private_port = ports[1]
            cmd = [IPTABLES_BINARY, '-t', 'nat', '-I', 'PREROUTING', '-p',
                   'tcp', '-d', config.PUBLIC_IP, '--dport', public_port, '-j',
                   'DNAT', '--to-destination',
                   '{0}:{1}'.format(machine['private_ip'],
                                    private_port)]
            log(' Private IP and port ' +
                '{}:{}'.format(machine['private_ip'],
                               private_port))
            log(' Public IP and port ' +
                '{}:{}'.format(config.PUBLIC_IP,
                               public_port))
            logged_call(cmd, config)
            cmds.append(' '.join(cmd))

        return (cmds)


def read_config(filename):
    return (SourceFileLoader('config', filename).load_module())


def main():
    hook, libvirt_object, action = sys.argv[0:3]
    hook = os.path.basename(hook)

    syslog.openlog(ident='libvirt-hook-' + hook + ' [' + str(os.getpid()) + ']:')

    log('{} {} for {}'.format(action.title(), hook, libvirt_object))

    try:
        # Import config.py
        config = read_config(CONFIG_FILENAME)

        if hook in ['qemu', 'lxc']:
            ctrl_machine(action, libvirt_object, config)
            pass

        if hook == 'network':
            ctrl_network(action, libvirt_object, config)
            pass

    except FileNotFoundError:
        log('No config.py.py found, terminating.', syslog.LOG_ERR)
        exit(0)
    except SyntaxError as exception:
        log('Syntax error in config.py.py configuration file.', syslog.LOG_ERR)
        log(str(exception.lineno) + ':' + str(exception.offset) +
            ': ' + exception.text, syslog.LOG_ERR)
        exit(1)


if __name__ == '__main__':
    main()
    exit(0)
