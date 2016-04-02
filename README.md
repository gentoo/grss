Description

The Gentoo Reference System (GRS) Suite is a set of tools for building and
maintaining a well defined Gentoo system in which all choices in building the
system are predefined in configuration files housed on a central git
repository. All systems built according to a particular GRS spec should be
identical. As a "from source" distribution, Gentoo allows a large degree of
customization. The space of all possible packages and USE flags is vast, not to
speak of more radical choices such as different kernels (eg. Linux or FreeBSD),
executable formats (eg. ELF or Mach-O), different C Standard Libraries (eg.
glibc, uClibc or musl) and different providers of core userland utilities (eg.
busybox or coreutils). In contrast to other distributions where each instance
of an installed system is nearly identical to another, the large array of
choice in Gentoo means that any two systems are unlikely to be sufficiently
similar that executables or libraries from one will "just work" on the other,
even if the architecture and other hardware factors are the same; assuming, of
course, there is no conscious effort to build identical systems. This is where
the Gentoo Release System (GRS) Suite comes in. It does precisely this, namely,
it provides an automated method for repeatedly and predictably generating
identical Gentoo systems.

GRS is designed to work roughly as follows: Periodic release tarballs are
generated which are "polished". For example, releases can provide
pre-configured display managers, windowing systems and desktop themes, even
user accounts and home directories. Installation should be as simple as
unpacking the release tarball on pre-formated partitions with minimal or no
further configuration. There is no need to build any packages or a kernel and
everything is ready to go out of the box. A release tarball can be downloaded
from some server or alternatively can be built locally. While these may not
initially be identical because they were build at different times, after
updating, both approaches should yield identical systems.

Updating a GRS system can proceed by either building packages locally, or
downloading pre-built binpkgs. As long as one does not deviate from the GRS
defined set of USE flags, maskings and other configuration parameters, both
approaches should yield identical systems. A GRS system is always a Gentoo
system, so at any time, one can elect to part ways from GRS and venture out on
one's own! The GRS Suite provides a utilities to make sure that configurations
in /etc/portage are properly maintained in a manner consistent with GRS, but
emerge and other portage utilities will always work. Even if one does deviate
from the GRS specs, it should be possible to return to strict GRS using the
Suite's utilities, provided one has not deviated too far.

GRS is provided by the app-portage/grs package. The same package is installed
on either a server responsible for building the release tarballs and binpkgs,
or on an actual GRS system. On the server, a daemon called grsrun will either
do a release run, in which case it builds the release tarballs, or it will do
an update run where it either builds or updates a bunch of extra binpkgs. For
example, for GRS = desktop-amd64-uclibc-hardened, the release run builds a
little under 900 packages and produces the polished release tarball, while the
update run builds/updates about 5700 packages. The first update run after a new
release is time consuming because some 5700 new packages must be built, but
subsequent update runs need only build packages which were bumped since the
last update run.

On the client, a utility called grsup acts as a wrapper to emerge. grsup will
both manage the configuration files in /etc/portage as well as either builds or
download the binpkg from a PORTAGE_BINHOST. After the initial installation of a
GRS system, one need only run grsup to bring it up to date. While releases
tarballs will be pushed out periodically, these are not used to update an
existing GRS system, only to start new one. Rather, one GRS release should
smoothly update to the next; in other words, each GRS release is equivalent to
the previous release plus any updates since. The only reason to push out a new
release tarball is to avoid having to subsequently push out a large number of
updates for each new installation.

Features:
* The GRS suite does not hard code any steps for the release or update runs.
Rather, a build script on the git repository describes the steps for building
each particular GRS system. This makes GRS runs highly flexible. One need only
transcribe the steps one would manually make in a chroot to build the system
into build script directives, and grsrun will automatically repeat them.
* It is possible to script a GRS system to do the equivalent of catalyst runs.
* The use of Linux cgroup make management easy. There is no need to trap or
propagate signals when writing the scripts that are to be run in the chroot. A
simple SIGTERM to grsrun will ensure that all children process no matter how
deep are properly terminated and that any bind-mounted filesystems are
unmounted.
* A GRS system acts as a "tinderbox lite" in that build failures are reported.
So as a GRS system evolves over time, as package are bumped, any breakages that
are introduced will be caught and reported. [TODO: get these reports
automatically into bugzilla.]

Authors:
* Anthony G. Basile <blueness@gentoo.org.>

Homepage:
* https://wiki.gentoo.org/wiki/Project:RelEng_GRS
