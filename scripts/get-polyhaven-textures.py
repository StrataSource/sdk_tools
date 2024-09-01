#!/usr/bin/env python3

import os
import subprocess
import argparse
import urllib.request
import urllib3
import string
import json

parser = argparse.ArgumentParser()
parser.add_argument('-u', '--url', action='append', dest='URLS', help='URL or name of a texture on polyhaven')
parser.add_argument('-o', required=True, dest='PATH', help='Output path')
parser.add_argument('-r', default='1k', dest='RES', choices=['1k', '2k', '4k', '8k', '16k'], help='Texture resolution')
parser.add_argument('-l', dest='LIST', type=str, help='List of textures to download')

MATERIAL_TEMPLATE = '''
PBR
{
	$$basetexture	"${color}"
	$$mraotexture	"${mrao}"
	$$bumpmap		"${disp}"
	$$parallax		"${use_parallax}"
	$$parallaxdepth	"0.01"
}
'''

def get_materials_subdir(path: str) -> str | None:
	path = path.replace('\\', '/')
	comps = path.split('/')
	comps.reverse()
	r = []
	for p in comps:
		if p != 'materials':
			r.insert(0, p)
		else:
			break
	if len(r) < len(comps):
		return '/'.join(r)
	return None


def get_texture(name: str, res: str, odir: str, mdir: str) -> bool:
	print(f'Fetching {name}...', end='', flush=True)
	types = ['nor_dx', 'ao', 'disp', 'diff', 'rough']
	textures = {}
	for type in types:
		url = f'https://dl.polyhaven.org/file/ph-assets/Textures/png/{res}/{name}/{name}_{type}_{res}.png'
		tex = f'{odir}/{name}_{type}_{res}.png'
		try:
			r = urllib3.request('GET', url)
			with open(tex, 'wb') as fp:
				fp.write(r.data)
			textures[type] = tex
		except Exception as e:
			print(tex)
			print(f'{url}: {e}')
			pass
	print('Done!')

	print(f'Converting {name} textures...', end='', flush=True)

	# Convert or pack normal map
	r = None
	if 'nor_dx' in textures:
		if 'disp' in textures:
			r = subprocess.run(['vtex2', 'pack', '-n', '-q', '--normal-map', textures['nor_dx'], '--height-map', textures['disp'], '-o', f'{odir}/{name}_n.vtf'])
		else:
			r = subprocess.run(['vtex2', 'convert', '-q', '-f', 'rgba8888', '-o', f'{odir}/{name}_n.vtf', textures['nor_dx']])

	if r.returncode != 0:
		print('Failed to pack normal')
		return False

	# Convert diffuse
	r = subprocess.run(['vtex2', 'convert', '-q', '-f', 'rgb888', '-o', f'{odir}/{name}_color.vtf', textures['diff']])
	if r.returncode != 0:
		print('Failed to convert diffuse')
		return False

	# Pack MRAO
	args = ['vtex2', 'pack', '--mrao', '-q', '-o', f'{odir}/{name}_mrao.vtf']
	
	if 'rough' in textures:
		args += ['--roughness-map', textures['rough']]
	else:
		args += ['--rougness-const', '1']
	
	if 'ao' in textures:
		args += ['--ao-map', textures['ao']]
	else:
		args += ['--ao-const', '1']

	if 'metal' in textures:
		args += ['--metalness-map', textures['metal']]
	else:
		args += ['--metalness-const', '0']

	r = subprocess.run(args=args)
	if r.returncode != 0:
		print('Failed to pack MRAO')
		return False

	# Generate VMT
	vmt = string.Template(MATERIAL_TEMPLATE).substitute({
			'mrao': f'{mdir}/{name}_mrao',
			'disp': f'{mdir}/{name}_n.vtf',
			'color': f'{mdir}/{name}_color.vtf',
			'use_parallax': '1' if 'disp' in textures else '0'
	})

	with open(f'{odir}/{name}.vmt', 'w') as fp:
		fp.write(vmt)

	print('Done!')
	return True


def check_programs():
	r = subprocess.run(['vtex2', '--version'], capture_output=True)
	if r.returncode != 0:
		print('Missing vtex2, make sure it\'s on your PATH!\nVTex2 can be downloaded here: https://github.com/StrataSource/vtex2/releases/latest')
		exit(1)


def main():
	args = parser.parse_args()
	check_programs()

	mdir = get_materials_subdir(args.PATH)

	r = 0
	for u in args.URLS:
		if not get_texture(u, args.RES, args.PATH, mdir):
			r = 1

	l = []
	if args.LIST is not None:
		with open(args.LIST, 'r') as fp:
			l = json.load(fp)

	for u in l:
		if not get_texture(u, args.RES, args.PATH, mdir):
			r = 1

	exit(r)

if __name__ == '__main__':
	main()
