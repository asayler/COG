#!/usr/bin/env python

import os
import time
import sys

while True:
    try:
        os.fork()
    except:
        sys.stderr.write("Forking failed\n")
        time.sleep(1)
