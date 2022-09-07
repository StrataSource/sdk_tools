convert_bik_to_webm.ps1 - A Windows PowerShell script to mass convert BIK files to WEBM.

Takes one argument, the full path to the folder with the BIKs you wish to convert.
This means you can drag the folder over the script in File Explorer and it will convert the
videos in that folder. It will place the converted WEBM files in a folder of the same name
next to this script.

This script optimizes quality over file size, but you should still see substantial
reductions in file size compared to BIK videos.

Requires the latest version of ffmpeg installed and placed on the PATH. If you don't know
what that means, download ffmpeg from https://www.gyan.dev/ffmpeg/builds/ffmpeg-git-full.7z
Extract this file, and copy <extracted folder>/bin/ffmpeg.exe to the same folder as this script.
