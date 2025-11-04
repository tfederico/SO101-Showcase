#!/bin/bash
set -euo pipefail

if [ $# -ne 1 ]; then
    echo "Usage: $0 <device-suffix>  (e.g. ACM0)" >&2
    exit 1
fi

suf="$1"
suf="${suf#/dev/}"   # strip optional /dev/
suf="${suf#tty}"     # strip optional leading tty

if [ -z "$suf" ]; then
    echo "Error: empty device suffix" >&2
    exit 1
fi

dev="/dev/tty${suf}"

if [ ! -e "$dev" ]; then
    echo "Error: device '$dev' does not exist" >&2
    exit 1
fi

sudo chmod 666 -- "$dev"
