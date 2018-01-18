# python 3

from __future__ import print_function
import os
import sys
from shutil import copyfile

# TODO improve arg parsing (use a library)
renames = sys.argv[1].strip()

force = False
if len(sys.argv) > 2:
    force = sys.argv[2].strip() == '-f'
    if force:
        print("-f detected: will overwrite files")

with open(renames, "r") as f:
    while True:
        x = f.readline()

        # TODO allow for empty lines in the input file -- only stop at end of file
        if x is None or x.strip() == '': break

        args = x.split(',')

        a = args[0].strip()
        b = args[1].strip()

        print(a, end = " ")
        print(" --> ", end = " ")
        print(b)

        try:
            copyfile(a, b)
        except FileNotFoundError as e:
            print(e)
        except FileExistsError as e:
            if force:
                print("Overwriting {}".format(b))
                os.remove(b)
                copyfile(a, b)
            else:
                print(e)
