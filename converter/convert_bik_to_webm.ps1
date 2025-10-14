#!/usr/bin/env pwsh
param(
    [parameter(mandatory)]
    [string] $BIKDir
)

Get-ChildItem -Path $BIKDir -Filter *.bik | Foreach-Object {
	$WEBMRelDir = "$pwd" + '/' + (Split-Path -Path $BIKDir -Leaf)
	if (!(Test-Path $WEBMRelDir -PathType Container)) {
		New-Item -ItemType Directory -Force -Path $WEBMRelDir
	}
	$FileName = $WEBMRelDir + '/' + ($_.Name -replace "bik$", "webm")

	ffmpeg -y -i $_.FullName -codec:v libvpx-vp9 -crf 16 -b:v 0 -map 0:v -codec:a libvorbis -map 0:a $FileName
}
