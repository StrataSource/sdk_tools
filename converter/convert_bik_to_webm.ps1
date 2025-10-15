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

	ffmpeg -y -i $_.FullName -codec:v vp8 -crf 16 -b:v 8M -map 0:v -codec:a libvorbis -map 0:a? $FileName
}
