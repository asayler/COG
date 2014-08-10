# Andy Sayler
# Summer 2014
# Univerity of Colorado

ECHO = @echo

PYTHON = python
PIP = pip
PYLINT = pylint

UNITTEST_PATTERN = '*_test.py'

COGS = cogs

.PHONY: all test clean

all:
	$(ECHO) "This is a python project; nothing to build!"

test:
	$(PYTHON) -m unittest discover -v -p $(UNITTEST_PATTERN)

clean:
	$(RM) *.pyc
	$(RM) *~
