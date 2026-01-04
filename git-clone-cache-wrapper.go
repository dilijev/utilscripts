package main

import (
	"crypto/sha256"
	"fmt"
	"io"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"strings"
	"time"
)

func main() {
	realGit, err := findRealGit()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error: %v\n", err)
		os.Exit(1)
	}

	if !hasClone(os.Args[1:]) {
		passThrough(realGit, os.Args[1:])
		return
	}

	cacheDir := getCacheDir()
	if err := os.MkdirAll(cacheDir, 0755); err != nil {
		fmt.Fprintf(os.Stderr, "Error creating cache: %v\n", err)
		os.Exit(1)
	}

	url := extractURL(os.Args[1:])
	if url == "" || isLocalPath(url) {
		passThrough(realGit, os.Args[1:])
		return
	}

	cacheKey := fmt.Sprintf("%x", sha256.Sum256([]byte(url)))
	cacheMirror := filepath.Join(cacheDir, cacheKey)

	lg := logger{dir: cacheDir}
	lg.printf("Clone URL: %s", url)
	lg.printf("Cache key: %s", cacheKey)

	if _, err := os.Stat(cacheMirror); os.IsNotExist(err) {
		lg.printf("Initializing cache")
		if err := run(realGit, "clone", "--mirror", url, cacheMirror); err != nil {
			lg.printf("ERROR: Cache init failed")
			os.Exit(1)
		}
	} else {
		lg.printf("Updating cache")
		run(realGit, "-C", cacheMirror, "fetch", "--all")
	}

	args := insertReference(os.Args[1:], cacheMirror)
	cmd := exec.Command(realGit, args...)
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	cmd.Stdin = os.Stdin
	if err := cmd.Run(); err != nil {
		if e, ok := err.(*exec.ExitError); ok {
			os.Exit(e.ExitCode())
		}
		os.Exit(1)
	}
}

func findRealGit() (string, error) {
	self, _ := os.Executable()
	self, _ = filepath.Abs(self)

	for _, dir := range strings.Split(os.Getenv("PATH"), string(os.PathListSeparator)) {
		git := filepath.Join(dir, "git")
		if runtime.GOOS == "windows" {
			git += ".exe"
		}
		abs, _ := filepath.Abs(git)
		if abs == self {
			continue
		}
		if info, err := os.Stat(git); err == nil && !info.IsDir() {
			return git, nil
		}
	}
	return "", fmt.Errorf("git not found in PATH")
}

func hasClone(args []string) bool {
	for _, arg := range args {
		if arg == "clone" {
			return true
		}
	}
	return false
}

func extractURL(args []string) string {
	afterClone := false
	for i := 0; i < len(args); i++ {
		if args[i] == "clone" {
			afterClone = true
			continue
		}
		if !afterClone {
			continue
		}
		if strings.HasPrefix(args[i], "-") {
			if (args[i] == "--depth" || args[i] == "--single-branch" || args[i] == "--branch") && i+1 < len(args) {
				i++
			}
			continue
		}
		return args[i]
	}
	return ""
}

func isLocalPath(path string) bool {
	_, err := os.Stat(path)
	return err == nil
}

func insertReference(args []string, mirror string) []string {
	result := []string{}
	inserted := false
	for _, arg := range args {
		result = append(result, arg)
		if arg == "clone" && !inserted {
			inserted = true
			result = append(result, "--reference", mirror)
		}
	}
	return result
}

func passThrough(git string, args []string) {
	cmd := exec.Command(git, args...)
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	cmd.Stdin = os.Stdin
	if err := cmd.Run(); err != nil {
		if e, ok := err.(*exec.ExitError); ok {
			os.Exit(e.ExitCode())
		}
		os.Exit(1)
	}
}

func run(git string, args ...string) error {
	cmd := exec.Command(git, args...)
	cmd.Stdout = io.Discard
	cmd.Stderr = io.Discard
	return cmd.Run()
}

func getCacheDir() string {
	if dir := os.Getenv("GIT_CLONE_CACHE_DIR"); dir != "" {
		return dir
	}
	home, _ := os.UserHomeDir()
	return filepath.Join(home, ".git-clone-cache")
}

type logger struct {
	dir string
}

func (l *logger) printf(format string, args ...interface{}) {
	msg := fmt.Sprintf(format, args...)
	line := fmt.Sprintf("[%s] [git-clone-cache] %s\n", time.Now().Format("2006-01-02 15:04:05"), msg)
	fmt.Fprint(os.Stderr, line)

	if logFile, err := os.OpenFile(filepath.Join(l.dir, "git-clone-cache.log"), os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0644); err == nil {
		logFile.WriteString(line)
		logFile.Close()
	}
}
