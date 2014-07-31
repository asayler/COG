# Andy Sayler
# Summer 2014
# Univerity of Colorado

ECHO = @echo

SERVER = ./server
CLIENT = ./client

.PHONY: all reqs test clean

all:
	$(ECHO) "Top Level Makefile; Nothing To Build"

reqs:
	$(MAKE) -C $(SERVER) $@
	$(MAKE) -C $(CLIENT) $@

test:
	$(MAKE) -C $(SERVER) $@
	$(MAKE) -C $(CLIENT) $@

clean:
	$(RM) *~
	$(MAKE) -C $(SERVER) $@
	$(MAKE) -C $(CLIENT) $@
