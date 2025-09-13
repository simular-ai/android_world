#!/usr/bin/env python3
"""Print task names from android_world/task_metadata.json, one per line."""

import json
import os
import sys


def main() -> None:
    # repo_root/scripts/list_tasks.py -> repo_root
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(script_dir)
    tasks_json = os.path.join(repo_root, 'android_world', 'task_metadata.json')
    try:
        with open(tasks_json, 'r') as f:
            data = json.load(f)
    except Exception as e:
        print(f"ERROR: could not read {tasks_json}: {e}", file=sys.stderr)
        sys.exit(1)

    for item in data:
        name = item.get('task_name')
        if name:
            print(name)

    print(f"Total tasks: {sum(1 for item in data if item.get('task_name'))}")

if __name__ == '__main__':
    main()


