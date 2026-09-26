#!/usr/bin/env bash
# The chronicle's own build: its people pages from the owner's table, then its docs.
# Run from anywhere; the books' data/ is upstream's and must already be built.
#
#   bash campaign/build/build.sh
set -euo pipefail
cd "$(dirname "$0")/../.."
if [ -d ../notion-export ]; then python3 campaign/source/convert_people.py; else echo "campaign build: no ../notion-export — people pages left as committed"; fi
python3 campaign/build/build_docs.py
node --check campaign/data/docs.js
node --check campaign/site/site.js
echo "campaign build: OK"
