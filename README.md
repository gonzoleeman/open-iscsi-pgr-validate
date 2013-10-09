iSCSI/SCSI-3 Persistent Group Reservations Test Suite
=====================================================
This package is a test suite for SCSI-3 Persistent Group Reservations
(PGR) using an iSCSI transport. This project grew out of a need to
verify PGR functionality after a search for such functionality turned
up nothing.

This test suite uses Python and the nose testing package, which
is built on the built-in unittest testing package.

You must have 3 local devices that all point to the same iSCSI
target. This can be done, for example, using open-iscsi, by
setting up three different interface files for that target,
and logging on to the target (in the iSCSI sense) through each
of those three interfaces.

Set Up
======
Here is how to set things up using open-iscsi on SLE 11 SP2.

Create these three interface files:

File /etc/iscsi/ifaces/t1:

    iface.transport_name = tcp
    iface.initiatorname = iqn.2003-04.net.gonzoleeman:test11
    iface.net_ifacename = eth0

File /etc/iscsi/ifaces/t2:

    iface.transport_name = tcp
    iface.initiatorname = iqn.2003-04.net.gonzoleeman:test12
    iface.net_ifacename = eth0

File /etc/iscsi/ifaces/t3:

    iface.transport_name = tcp
    iface.initiatorname = iqn.2003-04.net.gonzoleeman:test13
    iface.net_ifacename = eth0

Set up your target at IP address TARGET_IP_ADDR.

Then run:

    # iscsiadm -m discovery -t st -p TARGET_IP_ADDR -I t1 -l
    ... (output from iscsiadm -- 3 lines)
    # iscsiadm -m discovery -t st -p TARGET_IP_ADDR -I t2 -l
    ... (output from iscsiadm -- 3 lines)
    # iscsiadm -m discovery -t st -p TARGET_IP_ADDR -I t3 -l
    ... (output from iscsiadm -- 3 lines)

You will now have 3 nodes for the same target, and udev should
have made 3 devices. Use "sg_inq" on each "/dev/sd?" device you
find that you think may be our discs. For example, if you start
out with two discs, e.g. "/dev/sda" and "/dev/sdb", after you take
the above steps you may see three new devices, e.g. "/dev/sdc",
"/dev/sdd", and "/dev/sde". These 3 new devices would then be
the ones you configure in tests/support/initiator.py as your three
test targets.
