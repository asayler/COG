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
_LIMIT_NPROC = 100 #Processes (per user e.g. shared)
_LIMIT_MEM = 100*MBYTE #Bytes
_LIMIT_NICE = 15 #Niceness

def sandbox(args):

    # TODO Add proper argument extraction
    limit_time_cpu = int(args[0])
    limit_time_wall = int(args[1])
    cmd = args[2:]
    if not len(cmd):
        raise TypeError("User must supply cmd")

    def limit():

        _RLIMIT_FSIZE = (_LIMIT_FSIZE, _LIMIT_FSIZE)
        _RLIMIT_NOFILE = (_LIMIT_NOFILE, _LIMIT_NOFILE)
        _RLIMIT_NPROC = (_LIMIT_NPROC, _LIMIT_NPROC)
        _RLIMIT_MEM = (_LIMIT_MEM, _LIMIT_MEM)

        resource.setrlimit(resource.RLIMIT_FSIZE, _RLIMIT_FSIZE)
        resource.setrlimit(resource.RLIMIT_NOFILE, _RLIMIT_NOFILE)
        resource.setrlimit(resource.RLIMIT_CPU, (limit_time_cpu, limit_time_cpu))
        resource.setrlimit(resource.RLIMIT_NPROC, _RLIMIT_NPROC)
        resource.setrlimit(resource.RLIMIT_AS, _RLIMIT_MEM)
        os.nice(_LIMIT_NICE)

    full_cmd = ["timeout", str(limit_time_wall)]
    full_cmd += cmd
    p = subprocess.Popen(full_cmd, preexec_fn=limit, close_fds=True)
    ret = p.wait()
    return ret

if __name__ == "__main__":

    sys.exit(sandbox(sys.argv[1:]))
