"""ai-happy-01 entry: writes the thank-you card (entry.png, drawn by draw.py) to /output/entry.png.

Standard library only, no network; the same bytes on every run.
Locally: MAKEFUN_OUTPUT_DIR=out python3 main.py
"""

import os
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")

os.makedirs(OUTPUT_DIR, exist_ok=True)
shutil.copyfile(os.path.join(HERE, "entry.png"), os.path.join(OUTPUT_DIR, "entry.png"))
