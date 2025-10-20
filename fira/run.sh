#!/bin/bash

# colorize stderr and suppress fontforge warnings ("The glyph named uni021A is mapped to U+0162.")
python3 add_toaq.py "$@" 2> >(grep -v mapped | sed $'s,.*,\e[91m&\e[m,' >&2)
