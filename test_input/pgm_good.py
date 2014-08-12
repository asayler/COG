#!/usr/bin/env python

import sys

if len(sys.argv) != 3:
    sys.stderr.write("Usage: {:s} <num> <num>\n".format(sys.argv[0]))
    exit(1)

x = int(sys.argv[1])
y = int(sys.argv[2])
s = x + y

print("{:d}".format(s))
exit(0)
