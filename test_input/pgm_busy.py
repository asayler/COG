#!/usr/bin/env python

import time

SEED = 333

while True:
    SEED %= 33
    SEED *= SEED
