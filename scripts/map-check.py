#!/usr/bin/env python3

# A lightweight tool for analyzing map contents

import os
import string
import argparse
from srctools.vmf import VMF
from srctools.keyvalues import Keyvalues
from srctools.filesys import FileSystem, VPKFileSystem, RawFileSystem, ZipFileSystem
import srctools.filesys as filesystem
import json
from utils.steamtools import get_appid_path

parser = argparse.ArgumentParser(description='Simple tool to check the asset contents of a VMF')
parser.add_argument('-i', required=True, type=str, help='Path to the map file')
parser.add_argument('--textures', '-t', default=True, action='store_true', dest='textures', help='Check textures')
parser.add_argument('--models', '-m', action='store_true', dest='models', help='Check models')
parser.add_argument('--entities', '-e', action='store_true', dest='ents', help='List entities')
parser.add_argument('-c', '--count', action='store_true', dest='count', help='Display counts next to the asset path')
parser.add_argument('-p', '--path', nargs=1, action='append', dest='paths', help='Search paths to look for assets')
parser.add_argument('--check', action='store_true', help='Run in check mode, checking if assets can be found')
parser.add_argument('-l', '--list', action='store_true', dest='list', help='Just display a list of the assets')
parser.add_argument('-v', '--verbose', action='store_true', dest='verbose', help='Run in chatty mode')
parser.add_argument('--path-file', type=str, dest='path_file', help='Load paths from a JSON file')
parser.add_argument('--encoding', type=str, dest='encoding', default='utf-8', help='Use encoding for the map file')

class SourceFileSystem:
	def __init__(self, paths: list[str]):
		self.fs: list[FileSystem] = []
		for p in paths:
			self.fs.append(filesystem.get_filesystem(p))

	def from_file(self, file: str):
		with open(file, 'r') as fp:
			self.conf = json.load(fp)

		subs = {
			"fileDir": os.path.dirname(file)
		}

		for name, desc in self.conf.items():
			path = ''
			if 'appid' in desc:
				path = get_appid_path(desc['appid'])
				if path is None:
					raise FileNotFoundError(f'Unable to find install path for {desc["appid"]}! Is it installed?')
			else:
				path = string.Template(desc['path']).substitute(subs)

			if 'mount' in desc:
				for m in desc['mount']:
					self.fs.append(filesystem.get_filesystem(f'{path}/{m}'))

	@staticmethod
	def _get_filename(path: str) -> str:
		p = path.split('/')
		return p[len(p)-1]

	def file_exists(self, path: str) -> bool:
		"""Check if a file path exists
		Handles case insensitivity for you.
		"""
		for f in self.fs:
			# VPK/ZIP is capable of case insensitive compare
			if isinstance(f, VPKFileSystem) or isinstance(f, ZipFileSystem):
				try:
					with f.open_bin(path):
						return True
				except:
					pass
			else:
				for d in f.walk_folder():
					if d.path.casefold() == path.casefold():
						return True
		return False

def main():
	args = parser.parse_args()
	
	content = ''
	with open(args.i, 'r', encoding=args.encoding) as fp:
		content = fp.read()
	
	kv = Keyvalues.parse(content)
	vmf = VMF.parse(kv)

	paths = [x[0] for x in args.paths] if args.paths is not None else []
	if args.verbose:
		print(f'Paths: {paths}')
	fs = SourceFileSystem(paths)
	fs.from_file(args.path_file)

	exit_code = 0

	textures = {}
	if args.textures:
		# Grab list of materials for each brush
		for brush in vmf.brushes:
			for side in brush.sides:
				if side.mat not in textures: textures[side.mat] = 0
				textures[side.mat] += 1

		# Also go through the entities for the brush entities
		for ent in vmf.entities:
			for side in ent.sides():
				if side.mat not in textures: textures[side.mat] = 0
				textures[side.mat] += 1

		if args.list:
			for tex, count in textures.items():
				if args.count:
					print('{:5d} {:s}'.format(count, tex))
				else:
					print('{:s}'.format(tex))
		else:
			for tex in textures.keys():
				if not fs.file_exists(f'materials/{tex}.vmt'):
					print(f'missing {tex}')
					exit_code = 1
				elif args.verbose:
					print(f'found {tex}')
	
	models = {}
	if args.models:
		# Grab list of models from all of the ents
		for ent in vmf.entities:
			for kv in ['model', 'viewmodel', 'worldmodel']:
				m = ent.get(kv, None)
				if m is not None:
					if m not in models: models[m] = 0
					models[m] += 1

		if args.list:
			for model, count in models.items():
				if args.count:
					print('{:5d} {:s}'.format(count, model))
				else:
					print('{:s}'.format(model))
		else:
			for model in models.keys():
				if not fs.file_exists(f'{model}'):
					print(f'missing {model}')
					exit_code = 1
				elif args.verbose:
					print(f'found {model}')

	ents = {}
	if args.ents and args.list:
		for ent in vmf.entities:
			c = ent.get('classname')
			if c is None: continue
			if c not in ents: ents[c] = 0
			ents[c] += 1

		for e, c in ents.items():
			if args.count:
				print('{:5d} {:s}'.format(c, e))
			else:
				print('{:s}'.format(e))

	exit(exit_code)


if __name__ == '__main__':
	main()
