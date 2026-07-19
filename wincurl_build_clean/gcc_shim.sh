#!/bin/bash
# If the script calls gcc with -V or -qversion, redirect it to --version
if [[ "$*" == *"-V"* ]] || [[ "$*" == *"-qversion"* ]]; then
    exec /usr/bin/gcc --version
else
    exec /usr/bin/gcc "$@"
fi
