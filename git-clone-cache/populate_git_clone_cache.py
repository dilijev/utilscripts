#!/usr/bin/env python3

import os
import sys
import hashlib
import subprocess
import shutil
from pathlib import Path


def find_real_git():
    """Find the real git binary, skipping the wrapper at ~/bin/git"""
    wrapper_path = Path(__file__).parent / "git"
    wrapper_resolved = wrapper_path.resolve()
    
    git_path = shutil.which("git")
    if git_path and Path(git_path).resolve() != wrapper_resolved:
        return git_path
    
    return None


def get_origin_url(repo_path, real_git):
    """Extract origin URL from a local git repo"""
    try:
        result = subprocess.run(
            [real_git, "-C", str(repo_path), "remote", "get-url", "origin"],
            capture_output=True,
            text=True,
            check=False
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    
    return None


def compute_cache_key(url):
    """Compute SHA256 hash of URL"""
    return hashlib.sha256(url.encode()).hexdigest()


def is_local_repo(path):
    """Check if path is a git repository"""
    path_obj = Path(path)
    return path_obj.is_dir() and path_obj.joinpath(".git").exists()


def run_git_command(cmd, args):
    """Run a git command and return success status"""
    print(f"[populate-git-cache] {cmd} {' '.join(args)}", file=sys.stderr)
    try:
        subprocess.run([cmd] + args, check=True, capture_output=True)
        return True
    except subprocess.CalledProcessError:
        return False


def populate_cache(url, cache_mirror, real_git, source_for_clone):
    """Create or update a cache entry"""
    if cache_mirror.exists():
        print(f"Updating: {url}")
        if run_git_command(
            real_git, ["-C", str(cache_mirror), "fetch", "--all"]
        ):
            print("  -> OK")
            return True
        else:
            print(f"ERROR: Failed to update cache for {url}", file=sys.stderr)
            return False
    else:
        print(f"Caching: {url}")
        if run_git_command(
            real_git, ["clone", "--mirror", source_for_clone, str(cache_mirror)]
        ):
            print(f"  -> {cache_mirror}")
            return True
        else:
            print(f"ERROR: Failed to cache {url}", file=sys.stderr)
            return False


def main():
    real_git = find_real_git()
    if not real_git or not os.access(real_git, os.X_OK):
        print("Error: Could not find git binary", file=sys.stderr)
        sys.exit(1)
    
    cache_dir = Path(
        os.environ.get(
            "GIT_CLONE_CACHE_DIR", 
            os.path.expanduser("~/.git-clone-cache")
        )
    )
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    if len(sys.argv) < 2:
        prog_name = Path(sys.argv[0]).name
        print(
            f"Usage: {prog_name} /path/to/repo1 [/path/to/repo2 ...] "
            "[https://url ...]",
            file=sys.stderr
        )
        sys.exit(1)
    
    for arg in sys.argv[1:]:
        arg_path = Path(arg)
        
        if is_local_repo(arg):
            url = get_origin_url(arg_path, real_git)
            if not url:
                print(
                    f"WARNING: No origin remote in {arg}, skipping",
                    file=sys.stderr
                )
                continue
            source_for_clone = arg
        elif arg_path.is_dir():
            print(f"ERROR: Not a git repo: {arg}", file=sys.stderr)
            continue
        else:
            url = arg
            source_for_clone = url
        
        cache_key = compute_cache_key(url)
        cache_mirror = cache_dir / cache_key
        
        populate_cache(url, cache_mirror, real_git, source_for_clone)
    
    print("Done.")


if __name__ == "__main__":
    main()
