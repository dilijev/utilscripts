import sys
import os
import hashlib

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
            print "Checking directory: %s" % dirpath
        
            for filename in filenames:
                full_path = os.path.join(dirpath, filename)
                hashobj = hash()
                for chunk in chunk_reader(open(full_path, 'rb')):
                    hashobj.update(chunk)
                file_id = (hashobj.digest(), os.path.getsize(full_path))
                duplicate = hashes.get(file_id, None)
                if duplicate:
                    print "\nDuplicate found:\n  [1] %s\n  [2] %s" % (full_path, duplicate)
                    if delete:
                        if os.path.dirname(full_path) == os.path.dirname(duplicate):
                            time1 = os.path.getmtime(full_path)
                            time2 = os.path.getmtime(duplicate)
                            
                            print "Files are in the same directory: deleting oldest"
                            
                            if time1 < time2:
                                print "Deleting:\n  [1] %s" % full_path
                                
                                try:
                                    os.remove(full_path)
                                except:
                                    print "Could not find file:\n  %s\nContinuing..." % full_path

                                hashes[file_id] = duplicate
                                
                            else:
                                print "Deleting:\n  [1] %s" % full_path

                                try:
                                    os.remove(full_path)
                                except:
                                    print "Could not find file:\n  %s\nContinuing..." % full_path

                                hashes[file_id] = duplicate
                    
                        else:
                            selection = raw_input("Which to delete? [1/2]> ")

                            if selection == "1":
                                print "Deleting:\n  [1] %s" % full_path

                                try:
                                    os.remove(full_path)
                                except:
                                    print "Could not find file:\n  %s\nContinuing..." % full_path

                                hashes[file_id] = duplicate

                            elif selection == "2":
                                print "Deleting:\n  [2] %s" % duplicate

                                try:
                                    os.remove(duplicate)
                                except:
                                    print "Could not find file:\n  %s\nContinuing..." % duplicate

                            else:
                                print "Not deleting either image"
                else:
                    hashes[file_id] = full_path

if sys.argv[1:]:
    if sys.argv[1] == "-d":
        if sys.argv[2:]:
            check_for_duplicates(sys.argv[2:], delete=True)
    else:
        check_for_duplicates(sys.argv[1:])
else:
    print "Please pass the paths to check as parameters to the script"