from __future__ import print_function
import os
import sys
import argparse

def main():
    parser = argparse.ArgumentParser(
        description="Rename files in batch from a CSV file (src,dst per line)."
    )
    parser.add_argument("renames", help="CSV file with lines: src,dst")
    parser.add_argument("-f", "--force", action="store_true", help="Overwrite destination files if they exist")
    args = parser.parse_args()

    if args.force:
        print("-f detected: will overwrite files")

    with open(args.renames, "r") as f:
        for x in f:
            # Allow for empty lines in the input file -- only stop at end of file
            if x is None or x.strip() == '':
                continue

            args_line = x.split(',')

            if len(args_line) < 2:
                print("Skipping malformed line:", x.strip())
                continue

            a = args_line[0].strip()
            b = args_line[1].strip()

            print(a, end=" ")
            print(" --> ", end=" ")
            print(b)

            try:
                os.rename(a, b)
            except FileNotFoundError as e:
                print(e)
            except FileExistsError as e:
                if args.force:
                    print("Overwriting {}".format(b))
                    os.remove(b)
                    os.rename(a, b)
                else:
                    print(e)

if __name__ == "__main__":
    main()
