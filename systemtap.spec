# Release number for rpm build.  Stays at 1 for new PACKAGE_VERSION increases.
%define release 5
# Version number of oldest elfutils release that works with systemtap.
%define elfutils_version 0.131

# Don't build on ppc for RHEL5
ExcludeArch: ppc

# Set bundled_elfutils to 0 on systems that have %{elfutils_version} or newer.
%if 0%{?fedora}
%define bundled_elfutils 1
%define sqlite 0
%if "%fedora" >= "6"
%define bundled_elfutils 0
%define sqlite 1
%endif
%endif

%if 0%{?rhel}
%define bundled_elfutils 1
%define sqlite 0
%if "%rhel" >= "6"
%define bundled_elfutils 0
%define sqlite 1
%endif
%endif

%if 0%{!?bundled_elfutils:1}
# Yo!  DO NOT TOUCH THE FOLLOWING LINE.
# You can use rpmbuild --define "bundled_elfutils 0" for a build of your own.
%define bundled_elfutils 1
%endif

%if 0%{!?sqlite:1}
# Yo!  DO NOT TOUCH THE FOLLOWING LINE.
# You can use rpmbuild --define "sqlite 1" for a build of your own.
%define sqlite 0
%endif

Name: systemtap
Version: 0.6.1
Release: %{release}%{?dist}
Summary: Instrumentation System
Group: Development/System
License: GPLv2+
URL: http://sourceware.org/systemtap/
Source: ftp://sourceware.org/pub/%{name}/releases/%{name}-%{version}.tar.gz
Patch100: systemtap-0.6.1-gcc43.diff
Patch101: systemtap-0.6.1-elfi.diff

BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

Requires: kernel >= 2.6.9-11
BuildRequires: libcap-devel
%if %{sqlite}
BuildRequires: sqlite-devel
Requires: sqlite
%endif
%if "%rhel" >= "5"
BuildRequires: crash-devel zlib-devel
%endif
# Requires: kernel-devel
# or is that kernel-smp-devel?  kernel-hugemem-devel?
Requires: gcc make
# Suggest: kernel-debuginfo
Requires: systemtap-runtime = %{version}-%{release}
Requires(pre): shadow-utils

%if %{bundled_elfutils}
Source1: elfutils-%{elfutils_version}.tar.gz
Patch1: elfutils-portability.patch
%define setup_elfutils -a1
%else
BuildRequires: elfutils-devel >= %{elfutils_version}
%endif

%description
SystemTap is an instrumentation system for systems running Linux 2.6.
Developers can write instrumentation to collect data on the operation
of the system.

%package runtime
Summary: Instrumentation System Runtime
Group: Development/System
License: GPLv2+
URL: http://sourceware.org/systemtap/
Requires: kernel >= 2.6.9-11

%description runtime
SystemTap runtime is the runtime component of an instrumentation
system for systems running Linux 2.6.  Developers can write
instrumentation to collect data on the operation of the system.

%package testsuite
Summary: Instrumentation System Testsuite
Group: Development/System
License: GPLv2+
URL: http://sourceware.org/systemtap/
Requires: systemtap dejagnu

%description testsuite
The testsuite allows testing of the entire SystemTap toolchain
without having to rebuild from sources.

%prep
%setup -q %{?setup_elfutils}
%patch100 -p1
%patch101 -p0

%if %{bundled_elfutils}
cd elfutils-%{elfutils_version}
%patch1 -p1
sleep 1
find . \( -name Makefile.in -o -name aclocal.m4 \) -print | xargs touch
sleep 1
find . \( -name configure -o -name config.h.in \) -print | xargs touch
cd ..
%endif

%build

%if %{bundled_elfutils}
# Build our own copy of elfutils.
%define elfutils_config --with-elfutils=elfutils-%{elfutils_version}

# We have to prevent the standard dependency generation from identifying
# our private elfutils libraries in our provides and requires.
%define _use_internal_dependency_generator	0
%define filter_eulibs() /bin/sh -c "%{1} | sed '/libelf/d;/libdw/d;/libebl/d'"
%define __find_provides %{filter_eulibs /usr/lib/rpm/find-provides}
%define __find_requires %{filter_eulibs /usr/lib/rpm/find-requires}

# This will be needed for running stap when not installed, for the test suite.
%define elfutils_mflags LD_LIBRARY_PATH=`pwd`/lib-elfutils
%endif

%if %{sqlite}
# Include the coverage testing support
%define sqlite_config --enable-sqlitedb
%endif

%configure %{?elfutils_config} %{?sqlite_config}
make %{?_smp_mflags}

# Fix paths in the example & testsuite scripts
find examples testsuite -type f -name '*.stp' -print0 | xargs -0 sed -i -r -e '1s@^#!.+stap@#!%{_bindir}/stap@'

# To avoid perl dependency, make perl sample script non-executable
chmod -x examples/samples/kmalloc-top

%install
rm -rf ${RPM_BUILD_ROOT}
make DESTDIR=$RPM_BUILD_ROOT install

# Because "make install" may install staprun with mode 04111, the
# post-processing programs rpmbuild runs won't be able to read it.
# So, we change permissions so that they can read it.  We'll set the
# permissions back to 04111 in the %files section below.
chmod 755 $RPM_BUILD_ROOT%{_bindir}/staprun

# Copy over the testsuite
cp -rp testsuite $RPM_BUILD_ROOT%{_datadir}/systemtap

if [ -f $RPM_BUILD_ROOT%{_libdir}/%{name}/staplog.so ]; then
	echo %{_libdir}/%{name}/staplog.so > runtime-addl-files.txt
else
	touch runtime-addl-files.txt
fi

%clean
rm -rf ${RPM_BUILD_ROOT}

%pre
getent group stapdev >/dev/null || groupadd -r stapdev
getent group stapusr >/dev/null || groupadd -r stapusr
exit 0

%files
%defattr(-,root,root)

%doc README AUTHORS NEWS COPYING examples

%{_bindir}/stap
%{_mandir}/man1/*
%{_mandir}/man5/*

%dir %{_datadir}/systemtap
%{_datadir}/systemtap/runtime
%{_datadir}/systemtap/tapset

%if %{bundled_elfutils}
%dir %{_libdir}/%{name}
%{_libdir}/%{name}/lib*.so*
%endif

%files runtime -f runtime-addl-files.txt
%defattr(-,root,root)
%attr(4111,root,root) %{_bindir}/staprun
%{_libexecdir}/systemtap
%{_mandir}/man8/*

%doc README AUTHORS NEWS COPYING

%files testsuite
%defattr(-,root,root)
%{_datadir}/systemtap/testsuite


%changelog
* Wed Feb 13 2008 Will Cohen <wcohen@redhat.com> - 0.6.1-5
- Correct elfi typo in runtime/stack-i386.c.

* Tue Feb 12 2008 Will Cohen <wcohen@redhat.com> - 0.6.1-4
- Add patch for gcc 4.3.

* Fri Feb  1 2008 Frank Ch. Eigler <fche@redhat.com> - 0.6.1-3
- Add zlib-devel dependency which is supposed to come from crash-devel.

* Fri Feb  1 2008 Frank Ch. Eigler <fche@redhat.com> - 0.6.1-2
- Process testsuite .stp files to fool "#! stap" dep. finder.

* Fri Jan 18 2008 Frank Ch. Eigler <fche@redhat.com> - 0.6.1-1
- Add crash-devel buildreq to build staplog.so crash(8) module.
- Many robustness & functionality improvements:

* Wed Dec  5 2007 Will Cohen <wcohen@redhat.com> - 0.6-2
- Correct Source to point to location contain code.

* Thu Aug  9 2007 David Smith <dsmith@redhat.com> - 0.6-1
- Bumped version, added libcap-devel BuildRequires.

* Wed Jul 11 2007 Will Cohen <wcohen@redhat.com> - 0.5.14-2
- Fix Requires and BuildRequires for sqlite.

* Tue Jul  2 2007 Frank Ch. Eigler <fche@redhat.com> - 0.5.14-1
- Many robustness improvements: 1117, 1134, 1305, 1307, 1570, 1806,
  2033, 2116, 2224, 2339, 2341, 2406, 2426, 2438, 2583, 3037,
  3261, 3282, 3331, 3428 3519, 3545, 3625, 3648, 3880, 3888, 3911,
  3952, 3965, 4066, 4071, 4075, 4078, 4081, 4096, 4119, 4122, 4127,
  4146, 4171, 4179, 4183, 4221, 4224, 4254, 4281, 4319, 4323, 4326,
  4329, 4332, 4337, 4415, 4432, 4444, 4445, 4458, 4467, 4470, 4471,
  4518, 4567, 4570, 4579, 4589, 4609, 4664

* Mon Mar 26 2007 Frank Ch. Eigler <fche@redhat.com> - 0.5.13-1
- An emergency / preliminary refresh, mainly for compatibility
  with 2.6.21-pre kernels.

* Mon Jan  1 2007 Frank Ch. Eigler <fche@redhat.com> - 0.5.12-1
- Many changes, see NEWS file.

* Tue Sep 26 2006 David Smith <dsmith@redhat.com> - 0.5.10-1
- Added 'systemtap-runtime' subpackage.

* Wed Jul 19 2006 Roland McGrath <roland@redhat.com> - 0.5.9-1
- PRs 2669, 2913

* Fri Jun 16 2006 Roland McGrath <roland@redhat.com> - 0.5.8-1
- PRs 2627, 2520, 2228, 2645

* Fri May  5 2006 Frank Ch. Eigler <fche@redhat.com> - 0.5.7-1
- PRs 2511 2453 2307 1813 1944 2497 2538 2476 2568 1341 2058 2220 2437
  1326 2014 2599 2427 2438 2465 1930 2149 2610 2293 2634 2506 2433

* Tue Apr  4 2006 Roland McGrath <roland@redhat.com> - 0.5.5-1
- Many changes, affected PRs include: 2068, 2293, 1989, 2334,
  1304, 2390, 2425, 953.

* Wed Feb  1 2006 Frank Ch. Eigler <fche@redhat.com> - 0.5.4-1
- PRs 1916, 2205, 2142, 2060, 1379

* Mon Jan 16 2006 Roland McGrath <roland@redhat.com> - 0.5.3-1
- Many changes, affected PRs include: 2056, 1144, 1379, 2057,
  2060, 1972, 2140, 2148

* Mon Dec 19 2005 Roland McGrath <roland@redhat.com> - 0.5.2-1
- Fixed build with gcc 4.1, various tapset changes.

* Wed Dec  7 2005 Roland McGrath <roland@redhat.com> - 0.5.1-1
- elfutils update, build changes

* Fri Dec 02 2005  Frank Ch. Eigler  <fche@redhat.com> - 0.5-1
- Many fixes and improvements: 1425, 1536, 1505, 1380, 1329, 1828, 1271,
  1339, 1340, 1345, 1837, 1917, 1903, 1336, 1868, 1594, 1564, 1276, 1295

* Mon Oct 31 2005 Roland McGrath <roland@redhat.com> - 0.4.2-1
- Many fixes and improvements: PRs 1344, 1260, 1330, 1295, 1311, 1368,
  1182, 1131, 1332, 1366, 1456, 1271, 1338, 1482, 1477, 1194.

* Wed Sep 14 2005 Roland McGrath <roland@redhat.com> - 0.4.1-1
- Many fixes and improvements since 0.2.2; relevant PRs include:
  1122, 1134, 1155, 1172, 1174, 1175, 1180, 1186, 1187, 1191, 1193, 1195,
  1197, 1205, 1206, 1209, 1213, 1244, 1257, 1258, 1260, 1265, 1268, 1270,
  1289, 1292, 1306, 1335, 1257

* Wed Sep  7 2005 Frank Ch. Eigler <fche@redhat.com>
- Bump version.

* Wed Aug 16 2005 Frank Ch. Eigler <fche@redhat.com>
- Bump version.

* Wed Aug  3 2005 Martin Hunt <hunt@redhat.com> - 0.2.2-1
- Add directory /var/cache/systemtap
- Add stp_check to /usr/libexec/systemtap

* Wed Aug  3 2005 Roland McGrath <roland@redhat.com> - 0.2.1-1
- New version 0.2.1, various fixes.

* Fri Jul 29 2005 Roland McGrath <roland@redhat.com> - 0.2-1
- New version 0.2, requires elfutils 0.111

* Mon Jul 25 2005 Roland McGrath <roland@redhat.com>
- Clean up spec file, build bundled elfutils.

* Thu Jul 21 2005 Martin Hunt <hunt@redhat.com>
- Set Version to use version from autoconf.
- Fix up some of the path names.
- Add Requires and BuildRequires.

* Wed Jul 19 2005 Will Cohen <wcohen@redhat.com>
- Initial creation of RPM.
