#!/usr/bin/env python3

import os
import sys
import hashlib
import subprocess
import shutil
from pathlib import Path


def verbose(msg):
    print(f"[populate-git-cache][VERBOSE] {msg}", file=sys.stderr)


def find_real_git():
    """Find the real git binary, skipping the wrapper at ~/bin/git"""
    wrapper_path = Path(__file__).parent / "git"
    wrapper_resolved = wrapper_path.resolve()
    verbose(f"Looking for real git binary. Wrapper path: {wrapper_path}, resolved: {wrapper_resolved}")
    git_path = shutil.which("git")
    verbose(f"shutil.which('git') returned: {git_path}")
    if git_path and Path(git_path).resolve() != wrapper_resolved:
        verbose(f"Using git binary: {git_path}")
        return git_path
    verbose("Could not find a suitable git binary (skipping wrapper)")
    return None


def get_origin_url(repo_path, real_git):
    """Extract origin URL from a local git repo"""
    verbose(f"Getting origin URL for repo: {repo_path}")
    try:
        result = subprocess.run(
            [real_git, "-C", str(repo_path), "remote", "get-url", "origin"],
            capture_output=True,
            text=True,
            check=False
        )
        verbose(f"Command output: {result.stdout.strip()}, returncode: {result.returncode}")
        if result.returncode == 0:
            return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        verbose(f"Exception while getting origin URL: {e}")
    return None


def compute_cache_key(url):
    """Compute SHA256 hash of URL"""
    verbose(f"Computing cache key for URL: {url}")
    key = hashlib.sha256(url.encode()).hexdigest()
    verbose(f"Cache key: {key}")
    return key


def is_local_repo(path):
    """Check if path is a git repository"""
    path_obj = Path(path)
    verbose(f"Checking if path is a local git repo: {path}")
    is_repo = path_obj.is_dir() and path_obj.joinpath(".git").exists()
    verbose(f"is_local_repo({path}) = {is_repo}")
    return is_repo


def run_git_command(cmd, args):
    """Run a git command and return success status"""
    verbose(f"Running git command: {cmd} {' '.join(args)}")
    print(f"[populate-git-cache] {cmd} {' '.join(args)}", file=sys.stderr)
    try:
        result = subprocess.run([cmd] + args, check=True, capture_output=True)
        verbose(f"Command succeeded. stdout: {result.stdout}, stderr: {result.stderr}")
        return True
    except subprocess.CalledProcessError as e:
        verbose(f"Command failed: {e}. stdout: {e.stdout}, stderr: {e.stderr}")
        return False


def populate_cache(url, cache_mirror, real_git, source_for_clone):
    """Create or update a cache entry"""
    verbose(f"populate_cache called with url={url}, cache_mirror={cache_mirror}, source_for_clone={source_for_clone}")
    if cache_mirror.exists():
        print(f"Updating: {url}")
        verbose(f"Cache mirror exists: {cache_mirror}")
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
        verbose(f"Cache mirror does not exist, cloning to: {cache_mirror}")
        if run_git_command(
            real_git, ["clone", "--mirror", source_for_clone, str(cache_mirror)]
        ):
            print(f"  -> {cache_mirror}")
            return True
        else:
            print(f"ERROR: Failed to cache {url}", file=sys.stderr)
            return False


def main():
    verbose("Script started.")
    real_git = find_real_git()
    verbose(f"real_git resolved to: {real_git}")
    if not real_git or not os.access(real_git, os.X_OK):
        print("Error: Could not find git binary", file=sys.stderr)
        verbose("Exiting due to missing git binary.")
        sys.exit(1)
    
    cache_dir_env = os.environ.get("GIT_CLONE_CACHE_DIR")
    verbose(f"GIT_CLONE_CACHE_DIR env: {cache_dir_env}")
    cache_dir = Path(
        cache_dir_env if cache_dir_env else os.path.expanduser("~/.git-clone-cache")
    )
    verbose(f"Using cache_dir: {cache_dir}")
    cache_dir.mkdir(parents=True, exist_ok=True)
    verbose(f"Ensured cache_dir exists: {cache_dir}")
    
    if len(sys.argv) < 2:
        prog_name = Path(sys.argv[0]).name
        print(
            f"Usage: {prog_name} /path/to/repo1 [/path/to/repo2 ...] "
            "[https://url ...]",
            file=sys.stderr
        )
        verbose("Exiting due to missing arguments.")
        sys.exit(1)
    
    for arg in sys.argv[1:]:
        verbose(f"Processing argument: {arg}")
        arg_path = Path(arg)
        
        if is_local_repo(arg):
            verbose(f"Argument is a local repo: {arg}")
            url = get_origin_url(arg_path, real_git)
            if not url:
                print(
                    f"WARNING: No origin remote in {arg}, skipping",
                    file=sys.stderr
                )
                verbose(f"No origin remote found for {arg}, skipping.")
                continue
            source_for_clone = arg
        elif arg_path.is_dir():
            print(f"ERROR: Not a git repo: {arg}", file=sys.stderr)
            verbose(f"Argument is a directory but not a git repo: {arg}")
            continue
        else:
            verbose(f"Argument is treated as URL: {arg}")
            url = arg
            source_for_clone = url
        
        cache_key = compute_cache_key(url)
        cache_mirror = cache_dir / cache_key
        verbose(f"Cache mirror path: {cache_mirror}")
        
        populate_cache(url, cache_mirror, real_git, source_for_clone)
    
    print("Done.")
    verbose("Script finished.")


if __name__ == "__main__":
    main()
