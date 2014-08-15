#!/usr/bin/env python

import sys

def main(argv):

    if len(argv) == 0:
        x = int(raw_input("x: "))
        y = int(raw_input("y: "))
    elif len(argv) == 2:
        x = int(argv[0])
        y = int(argv[1])
    else:
        raise Exception("Provide either 2 args or none")

    if (x % 2) == 0:
        x += 1
    if (y % 3) == 0:
        y += 1

    s = x + y
    print("{:d}".format(s))

    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
