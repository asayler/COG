# Andy Sayler
# Compyright 2014, 2015, 2016
# Univerity of Colorado

ECHO = @echo

GIT = git

PYTHON := $(shell command -v python2 2> /dev/null)
ifndef PYTHON
	PIP := $(shell command -v python 2> /dev/null)
endif
ifndef PYTHON
	$(error Python not found)
endif
PIP := $(shell command -v pip2 2> /dev/null)
ifndef PIP
	PIP := $(shell command -v pip 2> /dev/null)
endif
ifndef PIP
	$(error Pip not found)
endif
PYLINT = pylint

REQUIRMENTS = requirments.txt
PYLINT_CONF = pylint.rc

UNITTEST_PATTERN = '*_test.py'

PYTHONPATH = $(shell readlink -f ./)
EXPORT_PATH = export PYTHONPATH="$(PYTHONPATH)"

COGS = cogs
MOODLE = moodle

.PHONY: all git reqs conf test clean

all:
	$(ECHO) "This is a python project; nothing to build!"

git:
	$(GIT) submodule init
	$(GIT) submodule update

reqs: $(REQUIRMENTS)
	$(PIP) install -r "$<" -U
	$(MAKE) -C $(COGS) $@
	$(MAKE) -C $(MOODLE) $@

conf:
	cp "./conf/sudoers.d/nobody" "/etc/sudoers.d/"
	chmod 440 "/etc/sudoers.d/nobody"
	cp "./conf/logrotate.d/cog-api" "/etc/logrotate.d/"
	cp "./conf/profile.d/Z95-cog.sh" "/etc/profile.d/"

lint: $(PYLINT_CONF)
	$(EXPORT_PATH) && $(PYLINT) --rcfile="$<" *.py
	$(EXPORT_PATH) && $(PYLINT) --rcfile="$<" $(COGS)

tests:
	$(EXPORT_PATH) && $(PYTHON) -m unittest discover -v -p $(UNITTEST_PATTERN)

clean:
	$(RM) *.pyc
	$(RM) *~
	$(MAKE) -C $(COGS) $@
	$(MAKE) -C $(MOODLE) $@
