# Andy Sayler
# Summer 2014
# Univerity of Colorado

ECHO = @echo

SERVER = ./server

.PHONY: all reqs test clean

all:
	$(ECHO) "Top Level Makefile; Nothing To Build"

reqs:
	$(MAKE) -C $(SERVER) $@

test:
	$(MAKE) -C $(SERVER) $@

clean:
	$(RM) *~
	$(MAKE) -C $(SERVER) $@
