#!/usr/bin/python3

"""Libvirt port-forwarding hook.

Libvirt hook for setting up iptables port-forwarding rules when using NAT-ed
networking on a host with a single public IP address.

Original version by "Sascha Peilicke <saschpe@gmx.de>" adapted for my use-case.

0.3.0:
======

 * Configuration in JSON format.

0.2.2:
======

 * Nicer iptables process calling.
 * Remove unneeded pass statements.
 * Source code documentation.
 * Removed log function.

0.2.1:
======

 * Renamed fwdconf to config.py
 * Rewrote unit tests
 * Add log function.

"""

__author__ = "Martin Bo Kristensen Groenholdt <martin.groenholdt@gmail.com>"
__version__ = "0.3.0"

import json
import os
import subprocess
import sys
import syslog

from hookjsonconf import HookConfig

# Path to the forwarding configuration file
CONFIG_PATH = os.getenv('CONFIG_PATH') or os.path.dirname(
    os.path.abspath(__file__))
# Name of the forwarding configuration file.
CONFIG_FILENAME = os.getenv('CONFIG_FILENAME') or os.path.join(CONFIG_PATH,
                                                               'config.json')
# Path of the iptables binary
IPTABLES_BINARY = os.getenv('IPTABLES_BINARY') or subprocess.check_output(
    ['which', 'iptables']).strip().decode('ascii')


def logged_call(args, config):
    """
    Log command and stdout from external call.

    :param args: A list of arguments used in the sub-process call.
    :param config: Configuration values from the configuration file.
    """

    # Log the actual command on debug.
    if config['debug']:
        syslog.syslog(syslog.LOG_DEBUG, ' '.join(args))

    # Call the command and pipe stdout to a place where we can use it.
    ret = subprocess.Popen(args, stdout=subprocess.PIPE)
    # Get stdout.
    # TODO Should be logging and checking stderr.
    ret = ret.communicate()[0].decode('ascii')
    # Log it as an alert if there is any output.
    if ret != '':
        syslog.syslog(syslog.LOG_ALERT, ret)


def ctrl_network(action, libvirt_object, config):
    """
    Set up/tear down the forwarding of incoming connections.

    :param action: libvirt hook action
    :param libvirt_object:
    :param config: Configuration values from the configuration file.
    :return: List of commands that has been executed.
    """
    cmds = list()
    network = None
    if libvirt_object in config['networks'].keys():
        network = config['networks'][libvirt_object]
    else:
        syslog.syslog('No network configuration, terminating.')
        exit(0)

    if action in ['unplugged']:
        syslog.syslog('Removing forwarding rule for network ' +
                      '{}'.format(network))
        cmd = [IPTABLES_BINARY, '-D', 'FORWARD', '-m', 'state', '-d',
               network, '--state', 'NEW,RELATED,ESTABLISHED', '-j',
               'ACCEPT']
        cmds.append(cmd)

    if action in ['plugged']:
        syslog.syslog('Adding forwarding rule for network ' +
                      '{}'.format(network))
        cmd = [IPTABLES_BINARY, '-I', 'FORWARD', '-m', 'state', '-d',
               network, '--state', 'NEW,RELATED,ESTABLISHED', '-j',
               'ACCEPT']
        cmds.append(cmd)

    for cmd in cmds:
        logged_call(cmd, config)

    # This is used for testing.
    cmds_strings = []
    for cmd in cmds:
        cmds_strings.append(' '.join(cmd))
    return (cmds_strings)


def ctrl_machine(action, libvirt_object, config):
    """
    Set up/tear down port forwarding for the individual machines.

    :param action: libvirt hook action
    :param libvirt_object:
    :param config: Configuration values from the configuration file.
    :return: List of commands that has been executed.
    """
    cmds = list()
    machine = {}
    if libvirt_object in config['machines'].keys():
        machine = config['machines'][libvirt_object]
    else:
        syslog.syslog('No forwarding configuration, terminating.')
        exit(0)

    if action in ['stopped', 'reconnect']:
        syslog.syslog('Remove {} forwarding rules'.format(libvirt_object))
        for ports in machine['port_map']:
            public_port = ports[0]
            private_port = ports[1]
            cmd = [IPTABLES_BINARY, '-t', 'nat', '-D', 'PREROUTING', '-p',
                   'tcp', '-d', config['public_ip'], '--dport',
                   public_port, '-j',
                   'DNAT', '--to-destination',
                   '{0}:{1}'.format(machine['private_ip'],
                                    private_port)]

            syslog.syslog(' Private IP and port ' +
                          '{}:{}'.format(machine['private_ip'],
                                         private_port))
            syslog.syslog(' Public IP and port ' +
                          '{}:{}'.format(config['public_ip'],
                                         public_port))
            cmds.append(cmd)

    if action in ['start', 'reconnect']:
        syslog.syslog('Insert {} forwarding rules'.format(libvirt_object))
        for ports in machine['port_map']:
            public_port = ports[0]
            private_port = ports[1]
            cmd = [IPTABLES_BINARY, '-t', 'nat', '-I', 'PREROUTING', '-p',
                   'tcp', '-d', config['public_ip'], '--dport', public_port, '-j',
                   'DNAT', '--to-destination',
                   '{0}:{1}'.format(machine['private_ip'],
                                    private_port)]
            syslog.syslog(' Private IP and port ' +
                          '{}:{}'.format(machine['private_ip'],
                                         private_port))
            syslog.syslog(' Public IP and port ' +
                          '{}:{}'.format(config['public_ip'],
                                         public_port))
            cmds.append(cmd)

        for cmd in cmds:
            logged_call(cmd, config)

        # This is used for testing.
        cmds_strings = []
        for cmd in cmds:
            cmds_strings.append(' '.join(cmd))
        return (cmds_strings)


def main():
    """
    Main entry point.
    """
    # Get the parameters from libvirt in to meaningful variables.
    hook, libvirt_object, action = sys.argv[0:3]
    # Isolate the executable name used to call us.
    hook = os.path.basename(hook)

    # Check for supported hook and action.
    if hook not in ['qemu', 'lxc', 'network']:
        exit(0)
    if action not in ['unplugged', 'plugged', 'stopped', 'start', 'reconnect']:
        exit(0)

    # Open a syslog logger that has the executable and the PID appended at the
    # beginning of each line
    syslog.openlog(
        ident='libvirt-hook-' + hook + ' [' + str(os.getpid()) + ']:')

    # Tell what libvirt wants us to do.
    syslog.syslog('{} {} for {}'.format(action.title(), hook, libvirt_object))

    try:
        # Import configuration
        json_config = HookConfig()
        config = None

        with open(CONFIG_FILENAME, 'r') as json_config_file:
            config = json_config.parse(json_config_file.read())

        try:
            # Find the hook function and call it.
            if hook in ['qemu', 'lxc']:
                ctrl_machine(action, libvirt_object, config)

            if hook == 'network':
                ctrl_network(action, libvirt_object, config)
        except FileNotFoundError as exception:
            syslog.syslog('Error executing iptables command, terminating.',
                          syslog.LOG_ERR)
            exit(0)

    except FileNotFoundError:
        syslog.syslog('No config.py found, terminating.', syslog.LOG_ERR)
        exit(0)
    except SyntaxError as exception:
        syslog.syslog('Syntax error in config.py configuration file.',
                      syslog.LOG_ERR)
        syslog.syslog('{}:{}: {}'.format(exception.lineno,
                                         exception.offset,
                                         exception.text), syslog.LOG_ERR)
        exit(1)
    except json.JSONDecodeError as jde:
        syslog.syslog('Error loading configuration file: {} in {} line {} char {}'.format(
                jde.msg, jde.doc, jde.lineno, jde.colno))
        exit(1)


if __name__ == '__main__':
    main()
    exit(0)
