open-iscsi-pgr-validate
=======================

Test suite that validates correct iSCSI Persistent Group Reservations



Version 0.1
===========
First version. This one requires 2 or 3 hosts talking to a SCSI target,
so it does not require iSCSI at all, but it does require ssh root password-
less access to all systems, so it is a pain to set up.

Development was done on openSUSE 12.2, using iscsitarget as the target and
open-iscsi as the initiators. The alternate hosts were running SLE 11 SP2.

To run these tests, use the "nose" package:

    zsh# nosetests -v

There are two "switches", which are hard-coded in the source file: "debug",
and "three_way". Set "debug" to True to spew volumes of debug messages, and
set "three_way" to True to enable using 3 hosts instead of 2.

The only test file is testReserve.py, which has a description of the hardware
setup required to use it.


Version 0.2
===========
Updated to use the interface ("iface") feature of open-iscsi to send from
multiple iSCSI initiators on a single host. This requires open-iscsi and
and iSCSI target, but only requires a single host.

Development is being done on SLE 11 SP2, since the "iface" feature of open-
iscsi works from here and does not seem to work from openSUSE 12.2 open-iscsi.
The target is still using iscsitarget on openSUSE 12.2 for initial development.
