LIBVIRT_HOOKS_DIR=/etc/libvirt/hooks

install:
	mkdir -p ${LIBVIRT_HOOKS_DIR}
	cp hooks.py ${LIBVIRT_HOOKS_DIR}
	if [ ! -f ${LIBVIRT_HOOKS_DIR}/config.py ] ; then cp config.py ${LIBVIRT_HOOKS_DIR} ; fi
	chmod +x ${LIBVIRT_HOOKS_DIR}/hooks.py
	ln -s ${LIBVIRT_HOOKS_DIR}/hooks.py ${LIBVIRT_HOOKS_DIR}/network
	ln -s ${LIBVIRT_HOOKS_DIR}/hooks.py ${LIBVIRT_HOOKS_DIR}/qemu
	ln -s ${LIBVIRT_HOOKS_DIR}/hooks.py ${LIBVIRT_HOOKS_DIR}/lxc



clean:
	rm ${LIBVIRT_HOOKS_DIR}/hooks.py
	rm ${LIBVIRT_HOOKS_DIR}/fwdconf.py
	rm ${LIBVIRT_HOOKS_DIR}/network
	rm ${LIBVIRT_HOOKS_DIR}/qemu
	rm ${LIBVIRT_HOOKS_DIR}/lxc
