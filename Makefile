# Andy Sayler
# Summer 2014
# Univerity of Colorado

ECHO = @echo

PYTHON = python
PIP = pip

REQUIRMENTS = requirments.txt

UNITTEST_PATTERN = '*_test.py'

COGS = ./cogs

.PHONY: all reqs test clean

all:
	$(ECHO) "This is a python project; nothing to build!"

reqs: $(REQUIRMENTS)
	$(PIP) install -r $(REQUIRMENTS) --use-mirrors

test:
	$(PYTHON) -m unittest discover -v -p $(UNITTEST_PATTERN)

clean:
	$(RM) *.pyc
	$(RM) $(COGS)/*.pyc
	$(RM) *~
	$(RM) $(COGS)/*~
