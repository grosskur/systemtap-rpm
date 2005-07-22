# Makefile for source rpm: systemtap
# $Id$
NAME := systemtap
SPECFILE = $(firstword $(wildcard *.spec))

include ../common/Makefile.common
