set files=*.gif
for %%f in (%files%) do ffmpeg -i "%%f" -acodec libvorbis -ac 1 -ab 96k -ar 48000 -b:v 1100k -maxrate 1100k -bufsize 1835k "%%f.webm"
mkdir old
move %files% old\
pause
