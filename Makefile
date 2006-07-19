# Makefile for source rpm: systemtap
# $Id: Makefile,v 1.7 2006/05/05 22:12:26 fche Exp $
NAME := systemtap
SPECFILE = $(firstword $(wildcard *.spec))

include ../common/Makefile.common

tarball = systemtap-$(VERSION).tar.gz

ifeq ($(clobber),t)
commit-check = :
else
commit-check = cvs -Q diff --brief > /dev/null 2>&1
endif

elfutils-version := $(shell awk '$$2 == "elfutils_version" { print $$3 }' \
				systemtap.spec)
eu-dir = ../../elfutils/devel
$(eu-dir)/elfutils.spec: FORCE
	cd $(@D) && cvs -Q update && $(commit-check)
$(eu-dir)/%.tar.gz: $(eu-dir)/elfutils.spec
	$(MAKE) -C $(@D) sources
$(eu-dir)/%.patch: $(eu-dir)/elfutils.spec ;

import-systemtap: $(tarball)
	$(commit-check) systemtap.spec
	tar -zf $(tarball) -xO '*.spec' > systemtap.spec
	$(MAKE) upload-systemtap
	touch $@

upload-systemtap: $(tarball) \
		  $(addprefix $(eu-dir)/,\
					 elfutils-$(elfutils-version).tar.gz \
					 elfutils-portability.patch)
	ln -f $(filter $(eu-dir)/%.tar.gz,$^) .
	ln -f $(filter $(eu-dir)/%.patch,$^) .
	$(MAKE) new-source FILES='$(filter-out %.patch,$^)'

copy-sources-%: import-systemtap
	cd ../$* && $(commit-check)
	cp -f sources elfutils-portability.patch ../$*
	ln -f elfutils-*.tar.gz $(tarball) ../$*

propagate-%: copy-sources-%
	cp -f systemtap.spec ../$*
	touch $@

# No automagic macros in beehive, only brew.
propagate-RHEL-4: copy-sources-RHEL-4 ../RHEL-4/systemtap.spec
	touch $@
propagate-FC-4: copy-sources-FC-4 ../FC-4/systemtap.spec
	touch $@

../RHEL-4/systemtap.spec: systemtap.spec import-systemtap
	@rm -f $@.new
	(echo '%define dist .el4'; \
	 echo '%define rhel 4'; \
	 cat systemtap.spec) > $@.new
	mv -f $@.new $@
../FC-4/systemtap.spec: systemtap.spec import-systemtap
	@rm -f $@.new
	(echo '%define dist .fc4'; \
	 echo '%define fedora 4'; \
	 cat systemtap.spec) > $@.new
	mv -f $@.new $@

.PRECIOUS: propagate-% tag-%

commit-%: propagate-%
	cd ../$* && cvs commit -m'Automatic update to $(VERSION)'
	touch $@

tag-%: commit-%
	cd ../$* && $(MAKE) tag
	touch $@

build-%: tag-%
	cd ../$* && $(MAKE) build
