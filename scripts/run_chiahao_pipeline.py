#!/usr/bin/env python3
"""Run Chiahao's cleaning, analysis, and visualization steps in order."""
from pathlib import Path
import subprocess,sys
ROOT=Path(__file__).resolve().parents[1]
for script in ['src/data/prepare_county_acs.py',
               'src/data/prepare_tract_acs.py',
               'src/analysis/summarize_daytime_changes.py',
               'src/visualization/plot_county_acs.py']:
    print('\n=== Running', script, '===',flush=True)
    subprocess.run([sys.executable,str(ROOT/script)],cwd=ROOT,check=True)
print('\nAll Chiahao pipeline stages completed.')
