python3 add_toaq.py 2> >(grep -v mapped | sed $'s,.*,\e[35m&\e[m,' >&2)
