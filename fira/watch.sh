while inotifywait -e close_write add_toaq.py; do echo; bash run.sh "$@" --preview; done
