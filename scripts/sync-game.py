#!/usr/bin/env python3

"""
A simple tool to sync files from an appid to a given directory

For example, if I want to copy in p2ce's bin, p2ce/bin and platform directories to 'mymod':

  ./scripts/sync-game.py -a 440000 -o path/to/mymod -d p2ce/bin -d platform -d bin

To first delete these directories from 'mymod' before copying, add the -c parameter.

"""

import argparse
import shutil
from utils.steamtools import *

def main():
	parser = argparse.ArgumentParser(usage="""
sync-game.py -a 440000 -d bin -d p2ce -o dir_where_i_want_the_files

Will copy in files from p2ce. The resulting layout will look like:
<p2ce-dir>/bin    ->     <out-dir>/bin
<p2ce-dir>/p2ce   ->     <out-dir>/p2ce
""")
	# NOTE: Using action=append instead of nargs='+' because python is stupid.
	parser.add_argument('-a', '--appid', type=int, required=True, help='AppID to copy files from')
	parser.add_argument('-d', '--dir', action='append', help='List of directorys to copy from within the AppID.')
	parser.add_argument('-f', '--file', action='append', help='Copy in a single file from the AppID')
	parser.add_argument('-o', '--out-dir', dest='OUT', type=str, required=True, help='Output directory')
	parser.add_argument('-c', '--clean', action='store_true', help='Delete destination dirs before copy. WARNING: This may delete your data!!!')
	parser.add_argument('-v', dest='VERBOSE', action='store_true', help='Run extra verbose-ly')
	parser.add_argument('--dry-run', action='store_true', dest='DRY', help='Dont actually copy or remove, just display the operations')
	args = parser.parse_args()

	# Need at least one dir or file
	if args.dir is None and args.file is None:
		print(f'ERROR: need at least one dir or file with -f/-d')
		exit(1)

	if args.dir is None: args.dir = []
	if args.file is None: args.file = []

	outpath = os.path.abspath(args.OUT)
	if not os.path.exists(outpath):
		print(f'ERROR: Output path "{outpath}" does not exist')
		exit(1)

	apppath = get_appid_path(args.appid)
	if apppath is None:
		print(f'ERROR: Unable to find install directory for {args.appid}')
		exit(1)
	print(f'Found {args.appid} install location at {apppath}')

	# Initial sanity check!
	anyFailed = False
	for d in args.dir + args.file:
		if not os.path.exists(f'{apppath}/{d}'):
			anyFailed = True
			print(f'Requested directory "{d}" does not exist in {args.appid}')
			print(f'  NOTE: Checked "{apppath}/{d}"')

	if anyFailed:
		print('ERROR: Failed to find some directories')
		exit(1)

	# Clean any dest dirs first, if requested
	if args.clean:
		for d in args.dir:
			try:
				if not args.DRY:
					shutil.rmtree(f'{outpath}/{d}')
				print(f'Cleaned {outpath}/{d}')
			except Exception as e:
				print(f'WARNING: Unable to remove {outpath}/{d}: {e}')

	# Copy in the dirs
	for d in args.dir:
		try:
			if not args.DRY:
				os.makedirs(f'{outpath}/{d}', exist_ok=True)
				shutil.copytree(f'{apppath}/{d}', f'{outpath}/{d}', dirs_exist_ok=True)
		except Exception as e:
			print(f'ERROR: Failed to copy {apppath}/{d} to {outpath}/{d}: {e}')
			exit(1)
		print(f'Copied {apppath}/{d} -> {outpath}/{d}')

	# Copy in the individual files
	for f in args.file:
		try:
			if not args.DRY:
				os.makedirs(f'{outpath}/{os.path.dirname(f)}', exist_ok=True)
				shutil.copy(f'{apppath}/{f}', f'{outpath}/{f}')
		except Exception as e:
			print(f'ERROR: Failed to copy {apppath}/{f} to {outpath}/{f}: {e}')
			exit(1)
		print(f'Copied {apppath}/{f} -> {outpath}/{d}')

	print(f'\nAll done!')

if __name__ == '__main__':
	main()
