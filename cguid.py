"""
cguid.py <GUID>

Where GUID is formatted as XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX
Where each X is a hex character /[\\dA-F]/i

http://icanhasguid.com/ can generate GUIDs in this form.

Outputs the GUID in the form of a C GUID struct literal.

Works with Python3 (tested with 3.6.0).
AFAIK, does not work with Python2, despite the print_function import (tested with 2.7.13).
"""

from __future__ import print_function

import re
import sys

GUID_RE = re.compile(r'.*([\dA-F]{8})-([\dA-F]{4})-([\dA-F]{4})-([\dA-F]{4})-([\dA-F]{12}).*', re.I)

def main():
    """ main """

    if len(sys.argv) >= 2:
        guid = sys.argv[1]
        print(guid)
        matches = GUID_RE.match(guid)
        if matches:
            print("Found match: " + guid)
            groups = matches.groups()
            group_3_pairs = re.match(r"(..)(..)", groups[3]).groups()
            group_4_pairs = re.match(r"(..)(..)(..)(..)(..)(..)", groups[4]).groups()
            formatted = ("{{ 0x{}, 0x{}, 0x{}, " \
                + "{{ 0x{}, 0x{}, 0x{}, 0x{}, 0x{}, 0x{}, 0x{}, 0x{} }} }};") \
                .format(groups[0], groups[1], groups[2], *group_3_pairs, *group_4_pairs)
            print(formatted)
        else:
            print("Not a valid GUID")
    else:
        print("Please provide a GUID formatted as XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX")

main()
