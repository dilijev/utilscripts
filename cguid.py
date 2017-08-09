"""
cguid.py <GUID>

Where GUID is formatted as XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX
Where each X is a hex character /[\\dA-F]/i

http://icanhasguid.com/ or uuidgen.exe (from the Windows 8+ SDK) can generate GUIDs in this form.

Outputs the GUID in the form of a C GUID struct literal.

Works with Python27 (tested with 2.7.13)
Works with Python3 (tested with 3.6.0)
"""

from __future__ import print_function

import re
import sys

GUID_RE = re.compile(r'.*([\dA-F]{8})-([\dA-F]{4})-([\dA-F]{4})-([\dA-F]{4})-([\dA-F]{12}).*', re.I)

def main():
    """ main """

    error = False
    if len(sys.argv) >= 2:
        guid = sys.argv[1]
        matches = GUID_RE.match(guid)
        if matches:
            print(guid)
            groups = matches.groups()
            group_3_pairs = re.match(r"(..)(..)", groups[3]).groups()
            group_4_pairs = re.match(r"(..)(..)(..)(..)(..)(..)", groups[4]).groups()
            pairs = list(group_3_pairs)
            pairs.extend(list(group_4_pairs))
            formatted = ("{{ 0x{}, 0x{}, 0x{}, " \
                + "{{ 0x{}, 0x{}, 0x{}, 0x{}, 0x{}, 0x{}, 0x{}, 0x{} }} }};") \
                .format(groups[0], groups[1], groups[2], *pairs)
            print(formatted)
        else:
            error = True
    else:
        error = True

    if error:
        print("Please provide a GUID formatted as XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX where each X is a Hex Digit (/[0-9A-F]/i)")

main()
