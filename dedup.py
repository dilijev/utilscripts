import sys
import os
import hashlib
import argparse
import json

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
        print(f"Could not load precedence rules: {e}")
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
            # Convert any hex string hashes back to bytes
            for fname, meta in record.items():
                if "hash" in meta and isinstance(meta["hash"], str):
                    try:
                        meta["hash"] = bytes.fromhex(meta["hash"])
                    except Exception:
                        pass
            print(f"Loaded hash record from {record_path}")
            return record
        except Exception as e:
            print(f"Could not load hash record {record_path}: {e}")
    print(f"Creating new hash record for {dirpath}")
    return {}

def save_dir_hash_record(dirpath, record_name, record):
    record_path = os.path.join(dirpath, record_name)
    # Convert any bytes in 'hash' fields to hex strings for JSON serialization
    serializable_record = {}
    for fname, meta in record.items():
        meta_copy = dict(meta)
        if isinstance(meta_copy.get("hash"), bytes):
            meta_copy["hash"] = meta_copy["hash"].hex()
        serializable_record[fname] = meta_copy
    try:
        with open(record_path, "w") as f:
            json.dump(serializable_record, f, indent=2, sort_keys=True)
        print(f"Saved hash record to {record_path}")
    except Exception as e:
        print(f"Could not save hash record {record_path}: {e}")

def get_file_hash(full_path, hashfunc, mtime, size, dir_record, filename, dirpath=None, record_name=None, record_hashes=False):
    rec = dir_record.get(filename)
    reason = None
    if rec is None:
        reason = "not in database"
    elif rec.get("mtime") != mtime:
        reason = "mtime changed"
    elif rec.get("size") != size:
        reason = "size changed"
    elif "hash" not in rec:
        reason = "hash missing"
    if reason:
        print(f"{reason} -> Computing hash for {full_path}")
        hashobj = hashfunc()
        with open(full_path, 'rb') as f:
            for chunk in chunk_reader(f):
                hashobj.update(chunk)
        file_hash = hashobj.digest()
        # Update record
        dir_record[filename] = {"mtime": mtime, "size": size, "hash": file_hash}
        # Write out the updated dir_record immediately after getting a new hash if requested
        if record_hashes and dirpath and record_name:
            save_dir_hash_record(dirpath, record_name, dir_record)
        return file_hash
    else:
        print(f"Using cached hash for {full_path}")
        return rec["hash"]

def check_for_duplicates(
    paths,
    delete=False,
    hashfunc=hashlib.sha256,
    precedence_rules=None,
    record_hashes=False,
    record_name=".dedup_hashes.json",
    min_filesize=1024,  # Ignore files smaller than 1 KB by default
    no_read_hashes=False
):
    hashes = {}
    dir_records = {}  # dirpath -> {filename: {mtime, size, hash}}
    ignore_files = {".DS_Store", record_name}
    for path in paths:
        for dirpath, dirnames, filenames in os.walk(path):
            print(f"Checking directory: {dirpath}")
            # Load hash record for this directory if present, unless bypassed
            if not no_read_hashes:
                dir_record = load_dir_hash_record(dirpath, record_name)
            else:
                dir_record = {}
            dir_records[dirpath] = dir_record

            for filename in filenames:
                if filename in ignore_files:
                    continue
                full_path = os.path.join(dirpath, filename)
                try:
                    stat = os.stat(full_path)
                except Exception as e:
                    print(f"Could not stat file {full_path}: {e}")
                    continue
                mtime = int(stat.st_mtime)
                size = stat.st_size
                if min_filesize > 0 and size < min_filesize:
                    # Ignore small files
                    continue
                file_hash = get_file_hash(
                    full_path, hashfunc, mtime, size, dir_record, filename,
                    dirpath, record_name, record_hashes
                )

                # Use (hash, size) as key for deduplication
                file_id = (file_hash, size)

                duplicate = hashes.get(file_id, None)
                if duplicate:
                    print(f"\nDuplicate found:\n  [1] {full_path}\n  [2] {duplicate}")
                    # Precedence rules logic
                    keep, to_delete = None, None
                    if precedence_rules:
                        keep, to_delete = match_precedence_rule(precedence_rules, full_path, duplicate)
                    if keep and to_delete:
                        print(f"Precedence rule: KEEP {keep}, DELETE {to_delete}")
                        if delete:
                            try:
                                os.remove(to_delete)
                                print(f"Deleted (by rule): {to_delete}")
                            except Exception as e:
                                print(f"Could not delete {to_delete}: {e}")
                        else:
                            print(f"[DRY RUN] Would delete (by rule): {to_delete}")
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
                                print(f"Deleting:\n  [1] {path1}")

                                try:
                                    os.remove(path1)
                                except:
                                    print(f"Could not find file:\n  {path1}\nContinuing...")
                                hashes[file_id] = path2

                            else:
                                print(f"Deleting:\n  [2] {path2}")
                                try:
                                    os.remove(path2)
                                except:
                                    print(f"Could not find file:\n  {path2}\nContinuing...")
                                hashes[file_id] = path1

                        else:
                            selection = input("Which to delete? [1/2] (type anything else to keep both)> ")

                            if selection == "1":
                                print(f"Deleting:\n  [1] {path1}")

                                try:
                                    os.remove(path1)
                                except:
                                    print(f"Could not find file:\n  {path1}\nContinuing...")

                                hashes[file_id] = path2

                            elif selection == "2":
                                print(f"Deleting:\n  [2] {path2}")

                                try:
                                    os.remove(path2)
                                except:
                                    print(f"Could not find file:\n  {path2}\nContinuing...")

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
    parser.add_argument("--record-hashes", action="store_true", help="Store and update per-directory JSON hash records for resumability")
    parser.add_argument("--record-name", default=".dedup_hashes.json", help="Filename for per-directory hash record (default: .dedup_hashes.json)")
    parser.add_argument("--min-filesize", type=int, default=1024, help="Ignore files smaller than this many bytes (default: 1024, set to 0 to disable)")
    parser.add_argument("--no-read-hashes", action="store_true", help="Do not read from per-directory hash record files even if present")
    args = parser.parse_args()

    if not args.record_hashes:
        print("Warning: --record-hashes not set, hashes will not be persisted for the next run.", file=sys.stderr)

    precedence_rules = load_precedence_rules(args.precedence_rules) if args.precedence_rules else None

    check_for_duplicates(
        args.paths,
        delete=args.delete,
        precedence_rules=precedence_rules,
        record_hashes=args.record_hashes,
        record_name=args.record_name,
        min_filesize=args.min_filesize,
        no_read_hashes=args.no_read_hashes
    )

if __name__ == "__main__":
    main()
