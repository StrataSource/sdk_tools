#!/usr/bin/env python3

import argparse
from utils.steamtools import get_appid_path

def main():
	parser = argparse.ArgumentParser(description='Finds the installation directory of a Steam app')
	parser.add_argument('-a', '--app', dest='APP', type=int, required=True, help='AppID to look for')
	args = parser.parse_args()
	p = get_appid_path(args.APP)
	if p is not None:
		print(p)
	else:
		exit(1)


if __name__ == '__main__':
	main()
