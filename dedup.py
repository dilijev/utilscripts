from __future__ import print_function
import sys
import os
import hashlib
import argparse
import json

try: input = raw_input
except NameError: pass

# compatible with python 2 and python 3

def chunk_reader(fobj, chunk_size=1024):
    """Generator that reads a file in chunks of bytes"""
    while True:
        chunk = fobj.read(chunk_size)
        if not chunk:
            return
        yield chunk

def load_precedence_rules(path):
    if not path:
        return []
    try:
        with open(path, "r") as f:
            rules = json.load(f)
            # Each rule should be a dict with 'keep' and 'delete' keys
            return rules if isinstance(rules, list) else []
    except Exception as e:
        print("Could not load precedence rules: %s" % e)
        return []

def match_precedence_rule(rules, path1, path2):
    # Returns (keep_path, delete_path) if a rule matches, else (None, None)
    for rule in rules:
        keep_prefix = rule.get("keep")
        delete_prefix = rule.get("delete")
        if keep_prefix and delete_prefix:
            # Normalize for OS
            kp = os.path.normpath(keep_prefix)
            dp = os.path.normpath(delete_prefix)
            p1 = os.path.normpath(path1)
            p2 = os.path.normpath(path2)
            if p1.startswith(kp) and p2.startswith(dp):
                return (path1, path2)
            if p2.startswith(kp) and p1.startswith(dp):
                return (path2, path1)
    return (None, None)

def check_for_duplicates(paths, delete=False, hash=hashlib.sha1, precedence_rules=None):
    hashes = {}
    for path in paths:
        for dirpath, dirnames, filenames in os.walk(path):
            print("Checking directory: %s" % dirpath)

            for filename in filenames:
                full_path = os.path.join(dirpath, filename)
                hashobj = hash()
                for chunk in chunk_reader(open(full_path, 'rb')):
                    hashobj.update(chunk)
                file_id = (hashobj.digest(), os.path.getsize(full_path))
                duplicate = hashes.get(file_id, None)
                if duplicate:
                    print("\nDuplicate found:\n  [1] %s\n  [2] %s" % (full_path, duplicate))
                    # Precedence rules logic
                    keep, to_delete = None, None
                    if precedence_rules:
                        keep, to_delete = match_precedence_rule(precedence_rules, full_path, duplicate)
                    if keep and to_delete:
                        print("Precedence rule: KEEP %s, DELETE %s" % (keep, to_delete))
                        if delete:
                            try:
                                os.remove(to_delete)
                                print("Deleted (by rule): %s" % to_delete)
                            except Exception as e:
                                print("Could not delete %s: %s" % (to_delete, e))
                        else:
                            print("[DRY RUN] Would delete (by rule): %s" % to_delete)
                        # Always keep the 'keep' file in the hashes map
                        hashes[file_id] = keep
                        continue
                    # ...existing code for interactive/manual selection...
                    if delete:
                        path1 = full_path
                        path2 = duplicate

                        if os.path.dirname(path1) == os.path.dirname(path2):
                            time1 = os.path.getmtime(path1)
                            time2 = os.path.getmtime(path2)

                            print("Files are in the same directory: deleting newest")

                            if time1 > time2:
                                print("Deleting:\n  [1] %s" % path1)

                                try:
                                    os.remove(path1)
                                except:
                                    print("Could not find file:\n  %s\nContinuing..." % path1)

                                hashes[file_id] = path2

                            else:
                                print("Deleting:\n  [2] %s" % path2)

                                try:
                                    os.remove(path2)
                                except:
                                    print("Could not find file:\n  %s\nContinuing..." % path2)

                                hashes[file_id] = path1

                        else:
                            selection = input("Which to delete? [1/2]> ")

                            if selection == "1":
                                print("Deleting:\n  [1] %s" % path1)

                                try:
                                    os.remove(path1)
                                except:
                                    print("Could not find file:\n  %s\nContinuing..." % path1)

                                hashes[file_id] = path2

                            elif selection == "2":
                                print("Deleting:\n  [2] %s" % path2)

                                try:
                                    os.remove(path2)
                                except:
                                    print("Could not find file:\n  %s\nContinuing..." % path2)

                            else:
                                print("Not deleting either image")
                    else:
                        print("[DRY RUN] Would prompt for deletion or keep both.")
                else:
                    hashes[file_id] = full_path

def main():
    parser = argparse.ArgumentParser(
        description="Find and optionally delete duplicate files in given directories."
    )
    parser.add_argument("paths", nargs="+", help="Directories to check for duplicates")
    parser.add_argument("-d", "--delete", action="store_true", help="Delete duplicates interactively or by rule")
    parser.add_argument("--precedence-rules", help="Path to precedence_rules.json for auto-deletion rules")
    args = parser.parse_args()

    precedence_rules = load_precedence_rules(args.precedence_rules) if args.precedence_rules else None

    check_for_duplicates(args.paths, delete=args.delete, precedence_rules=precedence_rules)

if __name__ == "__main__":
    main()
