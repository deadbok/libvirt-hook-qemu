
# Configuration for port forwarding hook.
#
# This file is used to configure libvirt virtual, machines running on a host
# with a single external IP address available, port forwarding.

# Debug information in syslog?
DEBUG = False

# Port mapping definitions for each machine
MACHINES = {
    'test': {
        'private_ip': '192.168.122.2',
        'port_map': [['2222', '22'], ['8002', '80']]
    }
}

# Virtual machine private networks
NETWORKS = {
    'default': '192.168.122.0/24'
}

#Public IP address
PUBLIC_IP = '192.168.0.166'







