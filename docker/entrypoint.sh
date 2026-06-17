#!/bin/sh
set -e
# Writable corpus/index/cache/uploads (image may ship without your private docs).
mkdir -p data/corpus data/uploads data/index data/cache
PORT="${PORT:-8501}"
exec streamlit run app/streamlit_app.py \
  --server.port="$PORT" \
  --server.address=0.0.0.0 \
  --server.headless=true \
  --server.fileWatcherType=none
