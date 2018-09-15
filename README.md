# libvirt port-forwarding hook

libvirt hook for setting up iptables port-forwarding rules when using NAT-ed
networking.

## Installation

To install the hook script and it's configuration files, simply use the
`Makefile`:

    $ sudo make install

Afterwards customize `/etc/libvirt/hooks/config.json` to your needs.
The files can be removed again with:

    $ sudo make uninstall

## hookctrl

Included in the installation is the `hookctrl` script. This is a command line utility to add and remove entries from config.json 

    ./hookctrl.py --help
    usage: hookctrl.py [-h] [--debug DEBUG] [--public_ip PUBLIC_IP]
                    [--cmd {add_machine,remove_machine,add_network,remove_network,add_port,remove_port}]
                    [--name NAME] [--private_ip PRIVATE_IP]
                    [--public_port PUBLIC_PORT] [--vm-port VM_PORT]
                    [--network NETWORK]

    Utility for adding, modifying and deleting machine definitions from the
    libvirt hook configuration file.

    optional arguments:
    -h, --help            show this help message and exit
    --debug DEBUG         Enable debugging when the hook is executed.
    --public_ip PUBLIC_IP
                            Public IP address of the libvirt host.
    --cmd {add_machine,remove_machine,add_network,remove_network,add_port,remove_port}
                            Sub entry commands.
    --name NAME           Name of the entry.
    --private_ip PRIVATE_IP
                            Set the private IP address of a machine.
    --public_port PUBLIC_PORT
                            Set the public port of the mapping.
    --vm-port VM_PORT     Set the machine port of the mapping.
    --network NETWORK     Set IP range of a network.

## Testing

Unit tests for hook code can be run using:

    $ ./test_hook.py

Unit tests for the hookctrl utility can be run using:

    $ ./test_hookcrtl.py

## Networking

This section describes the theory behind the generated iptables statements.

![Illustration of NAT-ed VM network ](doc/nat.png "[Illustration of NAT-ed VM network")

Packets arriving on the public interface are DNATed to the virtual machine.
This implements the actual port-forwarding.  Due to the way iptables is
implemented, the DNAT must occur in two chains: nat:PREROUTING for packets
arriving on the public interface, and nat:OUTPUT for packets originating on
the host.

We also add rules to the FORWARD chain to ensure the repsonses return.

Finally, packets originating on the guest and sent to the host's public IP
address need special handling.  They are DNATed back to the guest like all
other packets but, because the destination is now the same as the source,
the reply never leaves the guest.  Therefore, the host SNATs these packets
to ensure the reply returns over the bridge.

To see a real-world example, the ``test_setup`` function in test_qemu.py_
demonstrates a simple JSON configuration and the iptables rules that it produces.

## Authors

- Martin Grønholdt
- Sascha Peilicke
- Scott Bronson
