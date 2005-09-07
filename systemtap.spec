%define bundled_elfutils 0
%define elfutils_version 0.115

Name: systemtap
Version: 0.4
Release: 2
Summary: Instrumentation System
Group: Development/System
License: GPL
URL: http://sourceware.org/systemtap/
Source: ftp://sourceware.org/pub/%{name}/%{name}-%{version}.tar.gz

ExclusiveArch: %{ix86} x86_64

BuildRoot: %{_tmppath}/%{name}-root

Requires: kernel >= 2.6.9-11
Requires: kernel-devel
# or is that kernel-smp-devel?
Requires: gcc make
# Suggest: kernel-debuginfo

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

%prep
%setup -q %{?setup_elfutils}

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
elfutils_includedir="`pwd`/include-elfutils"
elfutils_libdir="`pwd`/lib-elfutils"
mkdir build-elfutils
cd build-elfutils
cat > configure <<\EOF
#!/bin/sh
exec ../elfutils-%{elfutils_version}/configure "$@"
EOF
chmod +x configure
%configure --enable-libebl-subdir=%{name}
make %{?_smp_mflags}
for dir in libelf libebl libdw libdwfl; do
  make -C $dir install includedir=$elfutils_includedir libdir=$elfutils_libdir
done
cd ..

# We'll configure with these options to use the local headers and libraries.
CPPFLAGS="-I${elfutils_includedir}"
LDFLAGS="-L${elfutils_libdir} -Wl,-rpath-link,${elfutils_libdir} \
-Wl,--enable-new-dtags,-rpath,%{_libdir}/%{name}"
export CPPFLAGS LDFLAGS

# We have to prevent the standard dependency generation from identifying
# our private elfutils libraries in our provides and requires.
%define _use_internal_dependency_generator	0
%define filter_eulibs() /bin/sh -c "%{1} | sed '/libelf/d;/libdw/d;/libebl/d'"
%define __find_provides %{filter_eulibs /usr/lib/rpm/find-provides}
%define __find_requires %{filter_eulibs /usr/lib/rpm/find-requires}

# This will be needed for running stap when not installed, for the test suite.
%define elfutils_mflags LD_LIBRARY_PATH=`pwd`/lib-elfutils
%endif

%configure
make %{?_smp_mflags}

%install
rm -rf ${RPM_BUILD_ROOT}

%makeinstall

%if %{bundled_elfutils}
installed_elfutils=${RPM_BUILD_ROOT}%{_libdir}/%{name}
mkdir -p ${installed_elfutils}
cp -P lib-elfutils/*.so* lib-elfutils/%{name}/*.so* ${installed_elfutils}/
%endif

mkdir -p $RPM_BUILD_ROOT/var/cache/systemtap

%check
make check %{?elfutils_mflags} || :

%clean
rm -rf ${RPM_BUILD_ROOT}

%files
%defattr(-,root,root)

%doc README AUTHORS NEWS COPYING

%{_bindir}/stap
%{_mandir}/man1/*
%{_mandir}/man5/*
%{_libexecdir}/systemtap/*

%dir %{_datadir}/systemtap
%{_datadir}/systemtap/runtime
%{_datadir}/systemtap/tapset

%dir %attr(0755,root,root) /var/cache/systemtap

%if %{bundled_elfutils}
%dir %{_libdir}/%{name}
%{_libdir}/%{name}/lib*.so*
%endif


%changelog
* Wed Sep  7 2005 Frank Eigler <fche@redhat.com> - 0.4-2
- Rebuilt for devel

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
