import os
import sys
import re
if sys.platform.startswith('win'):
	import winreg


def get_library_folders() -> list[str]:
	"""
	Returns a list of Steam libraries on this system

	Returns
	-------
	list[str]
		List of paths for the Steam libraries
	"""
	sp = ''
	if sys.platform.startswith('linux'):
		# Flatpak steam will also create the ~/.steam symlink
		sp = os.path.expanduser(f'~/.steam/steam/steamapps/libraryfolders.vdf')
	elif sys.platform.startswith('win'):
		# Registry trash for Windows.
		with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 'Software\\Wow6432Node\\Valve\\Steam', access=winreg.KEY_READ | winreg.KEY_WOW64_32KEY) as key:
			value = winreg.QueryValueEx(key, 'InstallPath')
			if value is not None and value[1] == winreg.REG_SZ:
				sp = f'{value[0]}\\steamapps\\libraryfolders.vdf'
			else:
				sp = f'C:\\Program Files (x86)\\Steam\\steamapps\\libraryfolders.vdf'
		# Check that the file *actually* exists; Steam in Proton doesn't use registry...
		if not os.path.exists(sp):
			sp = f'Z:{os.getenv("STEAM_COMPAT_CLIENT_INSTALL_PATH")}\\steam\\steamapps\\libraryfolders.vdf'.replace('/', '\\')

	with open(sp, 'r') as fp:
		return [x[1] for x in re.findall(r'\n\s+(\"path\")\s+\"(.+)\"\s*\n', fp.read())]


def get_library_for_appid(id: int) -> str | None:
	"""
	Returns the steam library path that contains the app

	Returns
	-------
	str|None
		Steam library that contains the appid
	"""
	folders = get_library_folders()
	if folders is None:
		return None

	for folder in folders:
		if os.path.exists(f'{folder}/steamapps/appmanifest_{id}.acf'):
			return folder
	return None


def get_appid_path(id: int) -> str | None:
	"""
	Tries to locate the AppID's install location based on Steam's libraryfolders.vdf

	Parameters
	----------
	id: int
		AppID to look for
	
	Returns
	-------
	str|None
		Install path location or None if it could not be found
	"""
	lf = get_library_for_appid(id)
	if lf is not None:
		am = {}
		with open(f'{lf}/steamapps/appmanifest_{id}.acf', 'r') as fp:
			m = re.findall(r'\n\s+(\"installdir\")\s+\"(.+)\"\s*\n', fp.read())
			if len(m) > 0:
				return f'{lf}/steamapps/common/{m[0][1]}'
	return None
