#!/usr/bin/env python

import os
import time

while True:
    try:
        os.fork()
    except:
        print("fork failed")
    time.sleep(1)
