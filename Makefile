# Andy Sayler
# Summer 2014
# Univerity of Colorado

ECHO = @echo

GIT = git

PYTHON = python
PIP = pip
PYLINT = pylint

REQUIRMENTS = requirments.txt
PYLINT_CONF = pylint.rc

UNITTEST_PATTERN = '*_test.py'

PYTHONPATH = $(shell readlink -f ./)
EXPORT_PATH = export PYTHONPATH="$(PYTHONPATH)"

COGS = cogs
MOODLE = moodle

.PHONY: all git reqs test clean

all:
	$(ECHO) "This is a python project; nothing to build!"

git:
	$(GIT) submodule init
	$(GIT) submodule update

reqs: $(REQUIRMENTS)
	$(PIP) install -r "$<" -U
	$(MAKE) -C $(COGS) $@
	$(MAKE) -C $(MOODLE) $@
	sudo apt-get install timeout

lint: $(PYLINT_CONF)
	$(EXPORT_PATH) && $(PYLINT) --rcfile="$<" $(COGS)
	$(EXPORT_PATH) && $(PYLINT) --rcfile="$<" $(MOODLE)

test:
	$(EXPORT_PATH) && $(PYTHON) -m unittest discover -v -p $(UNITTEST_PATTERN)

clean:
	$(RM) *.pyc
	$(RM) *~
	$(MAKE) -C $(COGS) $@
	$(MAKE) -C $(MOODLE) $@
