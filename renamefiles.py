from __future__ import print_function
import os
import sys

# TODO improve arg parsing (use a library)
renames = sys.argv[1].strip()
force = sys.argv[2].strip() == '-f'

if force:
    print("-f detected: will overwrite files")

with open(renames, "r") as f:
    while True:
        x = f.readline()
        if x is None or x.strip() == '': break

        args = x.split(',')

        a = args[0].strip()
        b = args[1].strip()

        print(a, end = " ")
        print(" --> ", end = " ")
        print(b)

        try:
            os.rename(a, b)
        except FileNotFoundError as e:
            print(e)
        except FileExistsError as e:
            if force:
                print("Overwriting {}".format(b))
                os.remove(b)
                os.rename(a, b)
            else:
                print(e)
