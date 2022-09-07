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

	ffmpeg.exe -y -i $_.FullName -codec:v libvpx-vp9 -crf 12 -b:v 0 -codec:a libvorbis $FileName
}
