#!/usr/bin/env python

import os
import sys
import resource
import subprocess
import time

KBYTE = 1024
MBYTE = KBYTE * KBYTE

_LIMIT_FSIZE = 100 #Blocks
_LIMIT_NOFILE = 100 #Files
_LIMIT_CPU = 1 #Seconds
_LIMIT_NPROC = 100 #Processes (per user e.g. shared)
_LIMIT_MEM = 100*MBYTE #Bytes
_LIMIT_NICE = 15 #Niceness
_LIMIT_TOTALTIME = 10 #Seconds

_RLIMIT_FSIZE = (_LIMIT_FSIZE, _LIMIT_FSIZE)
_RLIMIT_NOFILE = (_LIMIT_NOFILE, _LIMIT_NOFILE)
_RLIMIT_CPU = (_LIMIT_CPU, _LIMIT_CPU)
_RLIMIT_NPROC = (_LIMIT_NPROC, _LIMIT_NPROC)
_RLIMIT_MEM = (_LIMIT_MEM, _LIMIT_MEM)

def limit():
    resource.setrlimit(resource.RLIMIT_FSIZE, _RLIMIT_FSIZE)
    resource.setrlimit(resource.RLIMIT_NOFILE, _RLIMIT_NOFILE)
    resource.setrlimit(resource.RLIMIT_CPU, _RLIMIT_CPU)
    resource.setrlimit(resource.RLIMIT_NPROC, _RLIMIT_NPROC)
    resource.setrlimit(resource.RLIMIT_AS, _RLIMIT_MEM)
    os.nice(_LIMIT_NICE)

def sandbox(cmd):

    if not len(cmd):
        raise ValueError("User must supply cmd")

    full_cmd = ["timeout", str(_LIMIT_TOTALTIME)]
    full_cmd += cmd
    p = subprocess.Popen(full_cmd, preexec_fn=limit, close_fds=True)
    ret = p.wait()
    return ret

if __name__ == "__main__":

    sys.exit(sandbox(sys.argv[1:]))
