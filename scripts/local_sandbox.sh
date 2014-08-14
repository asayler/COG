#!/usr/bin/env bash

LIMIT_FILESIZE=100 #Blocks
LIMIT_MEM=102400 #kBytes
LIMIT_CPU=10 #Seconds
LIMIT_PROC=10 #Processes
LIMIT_NICE=15 #Niceness
LIMIT_TOTALTIME=30 #Seconds

ulimit -f ${LIMIT_FILESIZE} -m ${LIMIT_MEM} -t ${LIMIT_CPU} -u ${LIMIT_PROC}

nice -n ${LIMIT_NICE} timeout ${LIMIT_TOTALTIME} ${*}
