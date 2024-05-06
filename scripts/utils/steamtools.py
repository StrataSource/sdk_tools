#!/usr/bin/env python3

import vdf
import argparse
import os

def _find_appid_folder(id: int) -> str | None:
	lf = {}
	# Flatpak steam will also create the ~/.steam symlink
	with open(os.path.expanduser(f'~/.steam/steam/steamapps/libraryfolders.vdf'), 'r') as fp:
		lf = vdf.parse(fp)['libraryfolders']

	lfp = None
	for k in lf.keys():
		for m in lf[k]['apps'].keys():
			if int(m) == id:
				return lf[k]['path']
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
	lf = _find_appid_folder(id)
	if lf is not None:
		am = {}
		with open(f'{lf}/steamapps/appmanifest_{id}.acf', 'r') as fp:
			am = vdf.parse(fp)['AppState']
		return f'{lf}/steamapps/common/{am["installdir"]}'
	return None
