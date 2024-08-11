#!/usr/bin/env python3

# A lightweight tool for analyzing map contents

import os
import argparse
from srctools.vmf import VMF
from srctools.keyvalues import Keyvalues

parser = argparse.ArgumentParser(description='Simple tool to check the asset contents of a VMF')
parser.add_argument('-i', required=True, type=str, help='Path to the map file')
parser.add_argument('--textures', '-t', default=True, action='store_true', dest='textures', help='Check textures')
parser.add_argument('--models', '-m', action='store_true', dest='models', help='Check models')
parser.add_argument('-c', '--count', action='store_true', dest='count', help='Display counts next to the asset path')

def main():
	args = parser.parse_args()
	
	content = ''
	with open(args.i, 'r') as fp:
		content = fp.read()
	
	kv = Keyvalues.parse(content)
	vmf = VMF.parse(kv)

	textures = {}
	if args.textures:
		# Grab list of materials for each brush
		for brush in vmf.brushes:
			for side in brush.sides:
				if side.mat not in textures: textures[side.mat] = 0
				textures[side.mat] += 1

		for tex, count in textures.items():
			if args.count:
				print('{:5d} {:s}'.format(count, tex))
			else:
				print('{:s}'.format(tex))
	
	models = {}
	if args.models:
		# Grab list of models from all of the ents
		for ent in vmf.entities:
			for kv in ['model', 'viewmodel', 'worldmodel']:
				m = ent.get(kv, None)
				if m is not None:
					if m not in models: models[m] = 0
					models[m] += 1

		for model, count in models.items():
			if args.count:
				print('{:5d} {:s}'.format(count, model))
			else:
				print('{:s}'.format(model))

if __name__ == '__main__':
	main()
