#!/usr/bin/env python3
# coding=utf-8

import json
import pprint
import sys

#pp = pprint.PrettyPrinter(indent=2)
#with open('/var/www/html/lib/DKN.json', 'r') as handle:
#    programs = json.load(handle)
#    pp.pprint(programs)

pp = pprint.PrettyPrinter(indent=2)
programs = json.load(sys.stdin)
pp.pprint(programs)
