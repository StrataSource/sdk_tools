#!/usr/bin/env bash
# This script is public domain

set -e
cd "$(dirname "$0")/../bin/win64" # Assume we're starting in sdk_tools!

# !!! Change this hash when vcredist updates !!!
VCRUN2019_SHA="4c6c420cf4cbf2c9c9ed476e96580ae92a97b2822c21329a2e49e8439ac5ad30"
VCRUN2019_URL="https://aka.ms/vs/16/release/vc_redist.x86.exe"

PROG="$0"

# Defaults
[ -z "$WINEPREFIX" ] && export WINEPREFIX="$HOME/.wine"
[ -z "$WINE" ] && WINE="wine"
FORCE=0
GUI=1
SHORTCUT=1

function is-smart-term {
	if [ "$TERM" == "xterm-256color" ] || [ "$COLORTERM" == "truecolor" ]; then
		return 0
	fi
	return 1
}

function show-help {
	echo "Script to install Hammer prerequisite software into a wineprefix"
	echo "USAGE: $PROG [--force] [--help] [--prefix=wineprefix] [--wine=wine]"
	echo "  --force              - Skip all validity checks. This may be necessary if a download hash changes"
	echo "  --prefix=prefix      - Override default wineprefix"
	echo "  --wine=wine          - Use this wine executable"
	echo "  --no-gui             - Disable use of Zenity for UI"
	echo "  --no-shortcut        - Do not install shortcuts"
	if [ $# -gt 0 ]; then
		exit $1
	fi
}

function warn { 
	if is-smart-term; then
		printf '\e[93m'
	fi
	echo -e $@
	printf '\e[0m'
}

function error { 
	if is-smart-term; then
		printf '\e[91m'
	fi
	for a in $@; do
		echo -e "$a"
	done
	if [ $GUI -eq 1 ]; then
		zenity --error --text="$@"
	fi
	exit 1
}

function success { 
	if is-smart-term; then
		printf '\e[92m'
	fi
	for a in $@; do
		echo -e "$a"
	done
	printf '\e[0m'
}

function check-program {
	$1 &> /dev/null
	if [ $? -ne 0 ]; then
		if [ $# -gt 1 ]; then
			error $2
		else
			error "Could not find $1\nPlease install the corresponding package."
		fi
	fi
}

function download {
	F="$(mktemp).exe"
	wget -nv -O "$F" "$1"
	if [ $FORCE -eq 0 ]; then
		SUM="$(sha256sum "$F" | grep -Eo "^[^ ]+")"
		if [[ "$SUM" != "$2" ]]; then
			error "Checksum validation for file $1 failed!\nExpected: $2\nActual: $SUM\n\nYou may pass --force to disable this check"
			exit 1
		fi
	fi
	echo "$F"
}

# Argument parsing
for a in $@; do
	case $a in 
		--force)
			FORCE=1
			;;
		--prefix*)
			export WINEPREFIX="$(echo $a | sed 's/--prefix//g')"
			;;
		--wine*)
			WINE="$(echo $a | sed 's/--wine//g')"
			;;
		--help)
			show-help 0
			;;
		--no-gui)
			GUI=0
			;;
		--no-shortcut)
			SHORTCUT=0
			;;
		*)
			echo "Unknown argument $a"
			show-help 1
			;;
	esac
done

# Check for required software 
check-program "wget --version"
check-program "zenity --version"

# Before we do anything else, show the configuration dialog to the user, if GUI is enabled
if [ $GUI -ne 0 ]; then
	RESPONSE=$(zenity --forms \
		--text="WINE Hammer Setup" \
		--add-entry="WINE Prefix (Default: ~/.wine)" \
		--add-entry="WINE Path (Default: wine)" \
		--add-combo="Install .desktop shortcut? (Default: Yes)" \
		--combo-values="Yes|No" \
		--add-combo="Ignore errors? (--force)" \
		--combo-values="Yes|No"\
		--separator ",")
	IFS=','
	VALS=($RESPONSE)
	unset IFS
	[ ! -z "${VALS[0]}" ] && export WINEPREFIX="${VALS[0]}"
	[ ! -z "${VALS[1]}" ] && export WINE="${VALS[1]}"
	case "${VALS[2]}" in
		Yes)
			SHORTCUT=1
			;;
		No)
			SHORTCUT=0
			;;
		*)
			;;
	esac
	case "${VALS[3]}" in
		Yes)
			FORCE=1
			;;
		No)
			FORCE=0
			;;
		*)
			;;
	esac 
fi

# Check WINE in case specified in the GUI
check-program "$WINE --version"

# Check that the WINE version is new enough...
VERSION="$("$WINE" --version | grep -Eo "^(wine-)[0-9]")"
if [[ "$VERSION" == "*5" ]]  || [[ "$VERSION" == "*4" ]]; then
	if [ $FORCE -eq 0 ]; then
		error "Wine $VERSION is NOT supported! Please use WINE 6.0 or newer for Hammer\n\nYou may skip this check with --force"
		exit 1
	fi
fi

echo "Using prefix '$WINEPREFIX' with wine '$WINE'"

# Ask to create a prefix if it does not exist
if [ ! -d "$WINEPREFIX" ] && [ $GUI -ne 0 ]; then
	zenity --question --title="Prefix Does Not Exist." \
		--text="Prefix does not exist.\nWould you like to create it?" \
		--width=250
fi

if [ $FORCE -eq 1 ]; then
	warn "WARNING: Force skipping hash checks"
fi

pushd /tmp > /dev/null

#
# Install functions
#
function install-vcrun2019 {
	FILE=$(download "$VCRUN2019_URL" "$VCRUN2019_SHA")
	"$WINE" "$FILE"
	if [ $? -ne 0 ]; then
		error "Failed to install vcrun2019!\nYou may need to do this manually."
	fi
	rm -f "$FILE" || true # Eat errors here
}


# Ask the user what to install
if [ $GUI -ne 0 ]; then
	RESPONSE=$(zenity --list \
		--title="Dependency Installer" \
		--text="Select the dependencies to install" \
		--checklist \
		--column="Install" \
		--column="Component Name" \
		--width=350 \
		--separator="," \
		TRUE "vcrun2019")
	IFS=','
	VALS=($RESPONSE)
	unset IFS
	for i in "${VALS[$@]}"; do
		if [ "$i" == "vcrun2019" ]; then
			install-vcrun2019
		fi
	done
fi

popd > /dev/null

# Install shortcut
if [ $SHORTCUT -ne 0 ]; then

	# Complain if we already have a shortcut...
	P="$HOME/.local/share/applications/chaos-hammer.desktop"
	if [ -f "$P" ]; then
		if [ $GUI -ne 0 ]; then
			zenity --question --title="Overwrite Shortcut?" \
				--text="Shortcut for Chaos Hammer already exists.\nWould you like to overwrite it?" \
				--width=250
		fi
		warn "WARNING: Shortcut for Chaos Hammer already exists..overwriting..."
	fi

	# Download an icon
	wget -nv -O "$HOME/.local/share/icons/chaos-hammer.png" "https://raw.githubusercontent.com/ChaosInitiative/Chaos-FGD/master/hammer/resource/icons/hammer128.png"

	# Finally, generate desktop entry
	echo "[Desktop Entry]" > "$P"
	echo "Name=Chaos Hammer" >> "$P"
	echo "Comment=Map editing tool for Portal 2: Community Edition and other Chaos-based games" >> "$P"
	echo "Exec=env WINEPREFIX=\"$WINEPREFIX\" \"$WINE\" bin/win64/hammer.exe -winecompat" >> "$P"
	echo "Icon=chaos-hammer" >> "$P"
	echo "Terminal=false" >> "$P"
	echo "Type=Application" >> "$P"
	echo "Categories=Utility;Game;" >> "$P"
	echo "Path=$(realpath "$PWD"/../../)" >> "$P"
fi

zenity --width=250 --info --title="Install Finished" --text="Installation complete!\nYou may now launch hammer in WINE"
