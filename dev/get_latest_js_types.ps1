#!/usr/bin/env pwsh
# Get latest types file and plop it in panorama/scripts

$ErrorActionPreference = "Stop"
Set-Location "$PSScriptRoot/../../"

function Get-JSTypes {
	param (
		$GameDir
	)
	
	if (!(Test-Path -Path "$GameDir")) {
		return
	}
	
	Invoke-WebRequest https://github.com/panorama-languages-support/panorama-jsdoc-gen/releases/latest/download/types_$GameDir.zip -OutFile types.zip
	Expand-Archive -Path types.zip -DestinationPath .
	rm types.zip
	
	Move-Item -Force -Path "./__types_$GameDir.js" "$GameDir/panorama/scripts"
}

Get-JSTypes p2ce
Get-JSTypes momentum
