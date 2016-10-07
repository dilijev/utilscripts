from __future__ import print_function
import sys
import os
import hashlib

# compatible with python 2 and python 3

def chunk_reader(fobj, chunk_size=1024):
    """Generator that reads a file in chunks of bytes"""
    while True:
        chunk = fobj.read(chunk_size)
        if not chunk:
            return
        yield chunk

def check_for_duplicates(paths, delete=False, hash=hashlib.sha1):
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
                            selection = raw_input("Which to delete? [1/2]> ")

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
                    hashes[file_id] = full_path

if sys.argv[1:]:
    if sys.argv[1] == "-d":
        if sys.argv[2:]:
            check_for_duplicates(sys.argv[2:], delete=True)
    else:
        check_for_duplicates(sys.argv[1:])
else:
    print("Please pass the paths to check as parameters to the script")
