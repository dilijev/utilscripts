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

def load_dir_hash_record(dirpath, record_name):
    record_path = os.path.join(dirpath, record_name)
    if os.path.exists(record_path):
        try:
            with open(record_path, "r") as f:
                record = json.load(f)
            print("Loaded hash record from %s" % record_path)
            return record
        except Exception as e:
            print("Could not load hash record %s: %s" % (record_path, e))
    print("Creating new hash record for %s" % dirpath)
    return {}

def save_dir_hash_record(dirpath, record_name, record):
    record_path = os.path.join(dirpath, record_name)
    try:
        with open(record_path, "w") as f:
            json.dump(record, f, indent=2, sort_keys=True)
        print("Saved hash record to %s" % record_path)
    except Exception as e:
        print("Could not save hash record %s: %s" % (record_path, e))

def get_file_hash(full_path, hashfunc, mtime, size, dir_record, filename):
    # If present and mtime/size match, use cached hash
    rec = dir_record.get(filename)
    if rec and rec.get("mtime") == mtime and rec.get("size") == size and "hash" in rec:
        return rec["hash"]
    # Otherwise, compute hash
    hashobj = hashfunc()
    with open(full_path, 'rb') as f:
        for chunk in chunk_reader(f):
            hashobj.update(chunk)
    file_hash = hashobj.digest()
    # Update record
    dir_record[filename] = {"mtime": mtime, "size": size, "hash": file_hash}
    return file_hash

def check_for_duplicates(paths, delete=False, hashfunc=hashlib.sha256, precedence_rules=None, hash_record=False, record_name=".dedup_hashes.json"):
    hashes = {}
    dir_records = {}  # dirpath -> {filename: {mtime, size, hash}}
    for path in paths:
        for dirpath, dirnames, filenames in os.walk(path):
            print("Checking directory: %s" % dirpath)
            # Load or create hash record for this directory
            if hash_record:
                dir_record = load_dir_hash_record(dirpath, record_name)
            else:
                dir_record = {}
            dir_records[dirpath] = dir_record

            for filename in filenames:
                updated = False
                full_path = os.path.join(dirpath, filename)
                try:
                    stat = os.stat(full_path)
                except Exception as e:
                    print("Could not stat file %s: %s" % (full_path, e))
                    continue
                mtime = int(stat.st_mtime)
                size = stat.st_size
                file_hash = get_file_hash(full_path, hashfunc, mtime, size, dir_record, filename) if hash_record else None
                if hash_record and (filename not in dir_record or dir_record[filename].get("hash") != file_hash):
                    updated = True
                # Use (hash, size) as key for deduplication
                file_id = (file_hash if hash_record else None) or None
                if not file_id:
                    # fallback: always compute hash if not using hash_record
                    hashobj = hashfunc()
                    with open(full_path, 'rb') as f:
                        for chunk in chunk_reader(f):
                            hashobj.update(chunk)
                    file_id = (hashobj.digest(), size)
                else:
                    file_id = (file_hash, size)

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
                        hashes[file_id] = keep
                        continue
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

                # Save updated hash record in this directory after processing each file
                if hash_record and updated:
                    save_dir_hash_record(dirpath, record_name, dir_record)
                    updated = False

def main():
    parser = argparse.ArgumentParser(
        description="Find and optionally delete duplicate files in given directories."
    )
    parser.add_argument("paths", nargs="+", help="Directories to check for duplicates")
    parser.add_argument("-d", "--delete", action="store_true", help="Delete duplicates interactively or by rule")
    parser.add_argument("--precedence-rules", help="Path to precedence_rules.json for auto-deletion rules")
    parser.add_argument("--hash-record", action="store_true", help="Store and update per-directory JSON hash records for resumability")
    parser.add_argument("--record-name", default=".dedup_hashes.json", help="Filename for per-directory hash record (default: .dedup_hashes.json)")
    args = parser.parse_args()

    precedence_rules = load_precedence_rules(args.precedence_rules) if args.precedence_rules else None

    check_for_duplicates(
        args.paths,
        delete=args.delete,
        precedence_rules=precedence_rules,
        hash_record=args.hash_record,
        record_name=args.record_name
    )

if __name__ == "__main__":
    main()
