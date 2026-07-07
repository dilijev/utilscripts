@echo off
rem Convert all GIFs to MP4 with the same target bitrate (1100k)
setlocal enabledelayedexpansion

set "files=*.gif"
for %%f in (%files%) do (
    rem Build output name: same base name with .mp4 extension
    set "out=%%~nf.mp4"
    ffmpeg -i "%%f" ^
        -c:v libx264 -preset medium -pix_fmt yuv420p ^
        -b:v 1100k -maxrate 1100k -bufsize 1835k ^
        "!out!"
)

rem Archive the original GIFs
mkdir old 2>nul
move %files% old\

pause
