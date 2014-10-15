# Andy Sayler
# Test Make

CC = gcc
CFLAGS = -c -g -Wall -Wextra
LFLAGS = -g -Wall -Wextra

.PHONY: all clean

all: hello

hello: hello.o
	$(CC) $(LFLAGS) $^ -o $@

hello.o: hello.c
	$(CC) $(CFLAGS) $< -o $@

clean:
	$(RM) *.o
	$(RM) hello
	$(RM) *~
