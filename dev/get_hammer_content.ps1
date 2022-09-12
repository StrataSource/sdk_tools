#!/usr/bin/env pwsh
# Get FGD and hammer files from latest release, unzip, and toss em into game
# Autodetects mod

$confirm = Read-Host "This will overwrite your exist hammer cfg, are you sure you want to continue [Y/N]?"
if (!($confirm -ieq 'Y')) {
	Write-Output "Aborted."
	exit 0
}

Set-Location "$PSScriptRoot/../../"

function Download-FGD {
	param (
		$GameDir
	)

	if (!(Test-Path "$GameDir")) {
		return
	}
	
	Write-Output "Downloading fgd for $GameDir"
	$downloadroot = "https://github.com/ChaosInitiative/Chaos-FGD/releases/latest/download/"
	Invoke-WebRequest "$downloadroot/fgd-$GameDir.zip" -OutFile "fgd-$GameDir.zip"
	
	if (-not (Test-Path -Path "fgd-build")) {
		mkdir "fgd-build"
	}
	
	Expand-Archive "fgd-$GameDir.zip" -DestinationPath fgd-build
	rm "fgd-$GameDir.zip"
	
	# Nuke existing configs
	rm -rf "hammer/cfg"
	
	Copy-Item -Path ./fgd-build/* -Destination . -Recurse -Force
	rm -rf "fgd-build"
}

Download-FGD -GameDir p2ce
Download-FGD -GameDir momentum
