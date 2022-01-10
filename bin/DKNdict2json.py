#!/usr/bin/python3

import ast
import json
import sys

programs = ast.literal_eval(sys.stdin.read())

print(json.dumps(programs,sort_keys=True, indent=2))
