"""`python -m docs.guide [out]` builds 運作說明 (How it works) into out (_site by default) and prints the files it wrote."""

import sys
from pathlib import Path

from docs.guide.guide import build

print(*build(Path(sys.argv[1] if len(sys.argv) > 1 else "_site")), sep="\n")
