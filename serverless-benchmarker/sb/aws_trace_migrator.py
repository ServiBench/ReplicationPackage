import json
from pathlib import Path
import shutil


def migrate_traces(traces_path, replace=False):
    """Migrates a traces.json file in the old single line JSON format
    to the new format where each line contains a single JSON-formatted trace.
    Partial examples:
    Before:
    {"1-60be2454-2cb82d1221d24201751ea2e3": {"Id": "1-60be2454-2cb82d1221d24201751ea2e3", ... }, "1-60be244d-29f4c8461b7effa2caaa0848": {"Id": "1-60be244d-29f4c8461b7effa2caaa0848", ... }  # noqa: E501
    After:
    {"Id": "1-60be2454-2cb82d1221d24201751ea2e3", ... }
    {"Id": "1-60be244d-29f4c8461b7effa2caaa0848", ... }
    """
    with open(traces_path) as traces_file:
        new_traces_path = Path(traces_path).parent / 'traces_v2.json'
        with open(new_traces_path, 'w') as new_traces_file:
            # NOTE: Loading potentially large (GBs) file into memory
            traces = json.load(traces_file)
            for trace in traces.values():
                new_traces_file.write(json.dumps(trace) + '\n')
    # Optionally replace old file
    if replace:
        shutil.move(new_traces_path, traces_path)
