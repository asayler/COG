#!/bin/sh

COG_PATH="/srv/@cog/COG/"

if [ -z "${PYTHONPATH}" ]
then
    export PYTHONPATH="${COG_PATH}"
else
    export PYTHONPATH="${PYTHONPATH}":"${COG_PATH}"
fi
