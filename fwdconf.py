
# Configuration for port forwarding hook.
#
# This file is used to configure libvirt virtual, machines running on a host
# with a single external IP address available, port forwarding.

# Debug information in syslog?
DEBUG = False

# Port mapping definitions for each machine
MACHINES = {
    'observium': {
        'private_ip': '192.168.122.2',
        'port_map': [['22', '2222'], ['80', '8002']]
    }
}

# Virtual machine private networks
NETWORKS = {
    'default': '192.168.122.0/24'
}

#Public IP address
PUBLIC_IP = '144.76.102.118'







