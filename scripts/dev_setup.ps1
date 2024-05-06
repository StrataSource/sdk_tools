#!/usr/bin/env pwsh

# Sets up git configuration for p2ce development. NOT needed for anyone with source code access,
# only for non-licensed devs.
# This will disable submodule updating for bin and platform

Set-Location "$PSScriptRoot/../../"

# Tell git NOT to update these submodules
git config submodule.bin.update none
git config submodule.platform.update none

# Kick off initial update of everything else
git submodule update --init --recursive
