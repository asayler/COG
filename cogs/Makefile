# Andy Sayler
# Summer 2014
# Univerity of Colorado

ECHO = @echo

PYTHON = python
PIP = pip
PYLINT = pylint

REQUIRMENTS = requirments.txt

UNITTEST_PATTERN = '*_test.py'

PYTHONPATH = $(shell readlink -f ../)
EXPORT_PATH = export PYTHONPATH="$(PYTHONPATH)"

COGS = cogs

.PHONY: all test clean

all:
	$(ECHO) "This is a python project; nothing to build!"

reqs: $(REQUIRMENTS)
	$(PIP) install -r "$<" -U

test:
	$(EXPORT_PATH) && $(PYTHON) -m unittest discover -v -p $(UNITTEST_PATTERN)

clean:
	$(RM) *.pyc
	$(RM) *~
