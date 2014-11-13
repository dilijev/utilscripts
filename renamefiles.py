import os
import sys

renames = sys.argv[1].strip()

with open(renames, "r") as f:
    while True:
        x = f.readline()
        if x is None or x.strip() == '': break

        args = x.split(',')

        a = args[0].strip()
        b = args[1].strip()

        print a,
        print " --> ",
        print b

        os.rename(a, b)