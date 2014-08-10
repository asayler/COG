# Andy Sayler
# Summer 2014
# Univerity of Colorado

ECHO = @echo

PYTHON = python
PIP = pip
PYLINT = pylint

REQUIRMENTS = requirments.txt
PYLINT_CONF = pylint.rc

UNITTEST_PATTERN = '*_test.py'

COGS = cogs

.PHONY: all reqs test clean

all:
	$(ECHO) "This is a python project; nothing to build!"

reqs: $(REQUIRMENTS)
	$(PIP) install -r "$<"

lint: $(PYLINT_CONF)
	$(PYLINT) --rcfile="$<" $(COGS)

test:
	$(PYTHON) -m unittest discover -v -p $(UNITTEST_PATTERN)

clean:
	$(RM) *.pyc
	$(RM) *~
	$(MAKE) -C $(COGS) $@
