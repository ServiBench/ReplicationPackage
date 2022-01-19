#!/usr/bin/env python

"""Script to analyze new traces.json files.
Requires a Python environment with sb installed.
"""

from pathlib import Path
import os
from sb.sb import Sb


root_dir = Path(__file__).parent.parent.resolve()
data_source = os.environ.get('SB_DATA_SOURCE', None) or 'lg12'
default_data_path = root_dir / 'data' / data_source / 'raw'
apps_path = os.environ.get('SB_DATA_DIR', None) or default_data_path

# Force reanalysis (e.g., after updates to analyzer)
always_analyze = False

print(f"Analyze new traces.json files in {apps_path}")
traces = list(apps_path.glob('**/traces.json'))
sb = Sb()
for trace in traces:
	log_dir = trace.parent
	trace_breakdown = log_dir / 'trace_breakdown.csv'
	if always_analyze or not trace_breakdown.is_file():
		print(trace)
		sb.analyze_traces(trace)
