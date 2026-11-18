#!/bin/sh
# Python's standard library only; suppress generated files in the checkout.
set -eu
exec python3 -B "$(dirname "$0")/setup.py" "$@"
