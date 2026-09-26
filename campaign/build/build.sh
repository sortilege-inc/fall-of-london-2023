#!/usr/bin/env bash
# The chronicle's own build: its people pages and the GM seed from the owner's Notion export
# (../notion-export, beside the repo), the seed's every-word check, then its docs.
# Run from anywhere; the books' data/ is upstream's and must already be built.
#
#   bash campaign/build/build.sh
set -euo pipefail
cd "$(dirname "$0")/../.."
if [ -d ../notion-export ]; then
  python3 campaign/source/convert_people.py
  python3 campaign/source/absorb_notion.py
else
  echo "campaign build: no ../notion-export — people pages and the GM seed left as committed"
fi
python3 campaign/source/check_absorb.py 2>/dev/null || [ ! -d ../notion-export ]
python3 campaign/build/build_docs.py
node --check campaign/data/docs.js
node --check campaign/site/site.js
echo "campaign build: OK"
