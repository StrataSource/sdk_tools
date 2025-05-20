#!/usr/bin/env bash
# This script is public domain

set -e
cd "$(dirname "$0")/../bin/win64" # Assume we're starting in sdk_tools!

# !!! Change this hash when vcredist updates !!!
VCRUN2019_SHA="296f96cd102250636bcd23ab6e6cf70935337b1bbb3507fe8521d8d9cfaa932f"
VCRUN2019_URL="https://aka.ms/vs/16/release/vc_redist.x64.exe"

PROG="$0"

# Defaults
[ -z "$WINEPREFIX" ] && export WINEPREFIX="$HOME/.wine"
[ -z "$WINE" ] && WINE="wine"
[ -z "$PREFIX" ] && export PREFIX="$HOME/.local"
[ -z "$WINETRICKS" ] && WINETRICKS="winetricks"
FORCE=false
GUI=true
SHORTCUT=true

function supports-256-colors {
	(( $(tput colors) >= 256 ))
}

function show-help {
	echo "Script to install Hammer prerequisite software into a wineprefix"
	echo "USAGE: $PROG [--force] [--help] [--wineprefix=wineprefix] [--wine=wine] [--prefix=prefix]"
	echo "  --force              - Skip all validity checks. This may be necessary if a download hash changes"
	echo "  --prefix prefix      - Override default wineprefix"
	echo "  --wine wine          - Use this wine executable"
	echo "  --winetricks winetricks - Use this as the winetricks executable"
	echo "  --no-gui             - Disable use of Zenity for UI"
	echo "  --no-shortcut        - Do not install shortcuts"
	if [ $# -gt 0 ]; then
		exit $1
	fi
}

function warn { 
	if supports-256-colors; then
		printf '\e[93m'
	fi
	echo -e $@
	printf '\e[0m'
}

function error { 
	if supports-256-colors; then
		printf '\e[91m'
	fi
	echo -e "$@"
	if "$GUI"; then
		zenity --error --text="$@"
	fi
	exit 1
}

function success { 
	if supports-256-colors; then
		printf '\e[92m'
	fi
	echo -e "$@"
	printf '\e[0m'
}

function require-program {
	if ! command -v $1 &> /dev/null; then
		if [ $# -gt 1 ]; then
			error $2
		else
			error "Could not find $1\nPlease install the corresponding package."
		fi
		exit 127
	fi
}

function download {
	F="$(mktemp).exe"
	wget -nv -O "$F" "$1"
	if ! "$FORCE"; then
		SUM="$(sha256sum "$F" | grep -Eo "^[^ ]+")"
	fi
	echo "$F"
}

# Argument parsing
while test $# -gt 0; do
	case $1 in 
		--force)
			FORCE=true
			;;
		--wineprefix)
			export WINEPREFIX="$2"
			shift 2
			;;
		--prefix)
			export PREFIX="$2"
			shift 2
			;;
		--wine)
			WINE="$2"
			shift 2
			;;
		--winetricks)
			WINETRICKS="$2"
			shift 2
			;;
		--help)
			show-help 0
			;;
		--no-gui)
			GUI=false
			;;
		--no-shortcut)
			SHORTCUT=false
			GUI=0
			shift
			;;
		--no-shortcut)
			SHORTCUT=0
			shift
			;;
		*)
			echo "Unknown argument $a"
			show-help 1
			;;
	esac
done

# Check for required software 
require-program "wget"
"$GUI" && require-program "zenity"

# Before we do anything else, show the configuration dialog to the user, if GUI is enabled
if "$GUI"; then
	RESPONSE=$(zenity --forms \
		--text="WINE Hammer Setup" \
		--add-entry="WINE Prefix (Default: ~/.wine)" \
		--add-entry="WINE Path (Default: wine)" \
		--add-entry="Install Prefix (Default: ~/.local)" \
		--add-combo="Install .desktop shortcut? (Default: Yes)" \
		--combo-values="Yes|No" \
		--add-combo="Ignore errors? (--force)" \
		--combo-values="Yes|No"\
		--separator ",")
	IFS=','
	VALS=($RESPONSE)
	unset IFS
	[ ! -z "${VALS[0]}" ] && export WINEPREFIX="$(readlink -mf "$(eval echo "${VALS[0]}")")"
	[ ! -z "${VALS[1]}" ] && export WINE="${VALS[1]}"
	[ ! -z "${VALS[2]}" ] && export PREFIX="${VALS[2]}"
	case "${VALS[3]}" in
		Yes)
			SHORTCUT=true
			;;
		No)
			SHORTCUT=false
			;;
		*)
			;;
	esac
	case "${VALS[4]}" in
		Yes)
			FORCE=true
			;;
		No)
			FORCE=false
			;;
		*)
			;;
	esac 
fi

# Check WINE in case specified in the GUI
require-program "$WINE"

# Check that the WINE version is new enough...
VERSION="$("$WINE" --version | grep -Eo "^(wine-)[0-9]")"
if [[ "$VERSION" == "*5" ]]  || [[ "$VERSION" == "*4" ]]; then
	if ! "$FORCE"; then
		error "Wine $VERSION is NOT supported! Please use WINE 6.0 or newer for Hammer\n\nYou may skip this check with --force"
		exit 1
	fi
fi

echo "Using wineprefix '$WINEPREFIX' with wine '$WINE'"

# Ask to create a prefix if it does not exist
if [ ! -d "$WINEPREFIX" ] && "$GUI"; then
	zenity --question --title="WINE Prefix Does Not Exist." \
		--text="WINE Prefix does not exist.\nWould you like to create it?" \
		--width=250
fi

mkdir -p "$PREFIX/share/applications"
mkdir -p "$PREFIX/share/icons"

if "$FORCE"; then
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

function install-dxvk {
	echo "Installing dxvk..."
	if ! "$WINETRICKS" dlls dxvk; then
		error "Failed to install dxvk!\nYou may need to do this manually."
	fi
}

# Ask the user what to install
if "$GUI"; then
	RESPONSE=$(zenity --list \
		--title="Dependency Installer" \
		--text="Select the dependencies to install" \
		--checklist \
		--column="Install" \
		--column="Component Name" \
		--width=350 \
		--separator="," \
		TRUE "vcrun2019"\
		TRUE "dxvk")
	IFS=','
	VALS=($RESPONSE)
	unset IFS
	for i in "${VALS[@]}"; do
		echo $i
		install-$i
	done
fi

popd > /dev/null

# Install shortcut
if "$SHORTCUT"; then

	# Complain if we already have a shortcut...
	P="$PREFIX/share/applications/strata-hammer.desktop"
	if [ -f "$P" ]; then
		if "$GUI"; then
			zenity --question --title="Overwrite Shortcut?" \
				--text="Shortcut for Strata Hammer already exists.\nWould you like to overwrite it?" \
				--width=250
		fi
		warn "WARNING: Shortcut for Strata Hammer already exists..overwriting..."
	fi

	# Download an icon
	wget -nv -O "$PREFIX/share/icons/strata-hammer.png" "https://raw.githubusercontent.com/StrataSource/FGD/master/hammer/resource/icons/hammer128.png"

	# Finally, generate desktop entry
	echo "[Desktop Entry]" > "$P"
	echo "Name=Strata Hammer" >> "$P"
	echo "Comment=Map editing tool for Portal 2: Community Edition and other Strata-based games" >> "$P"
	echo "Exec=env WINEPREFIX=\"$WINEPREFIX\" \"$WINE\" bin/win64/hammer.exe -winecompat" >> "$P"
	echo "Icon=strata-hammer" >> "$P"
	echo "Terminal=false" >> "$P"
	echo "Type=Application" >> "$P"
	echo "Categories=Utility;Game;" >> "$P"
	echo "Path=$(realpath "$PWD"/../../)" >> "$P"
fi

echo "Install Finished"
echo "Installation complete!"
echo "You may now launch hammer in WINE"
"$GUI" && zenity --info --title="Install Finished" \
                      --text="Installation complete!\nYou may now launch hammer in WINE" \
                      --width=250
