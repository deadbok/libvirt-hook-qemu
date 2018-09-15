# Build all rule, only builds the package
all: install

.PHONY: tests
tests:
	./test_hook.py
	./test_hookctrl.py

.PHONY: install
install: tests /etc/libvirt/hooks/config.json
	install -d /etc/libvirt/hooks
	install hooks.py /etc/libvirt/hooks/
	install hookjsonconf.py /etc/libvirt/hooks/
	install hookctrl.py /etc/libvirt/hooks/hookctrl
	ln -sf /etc/libvirt/hooks/hooks.py /etc/libvirt/hooks/lxc
	ln -sf /etc/libvirt/hooks/hooks.py /etc/libvirt/hooks/qemu
	ln -sf /etc/libvirt/hooks/hooks.py /etc/libvirt/hooks/network

/etc/libvirt/hooks/config.json:
	install -d /etc/libvirt/hooks
	install config.json /etc/libvirt/hooks/

.PHONY: uninstall
uninstall:
	install /etc/libvirt/hooks/hooks.py
	install /etc/libvirt/hooks/hookjsonconf.py
	install /etc/libvirt/hooks/hookctrl
