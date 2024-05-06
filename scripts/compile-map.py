#!/usr/bin/env python3

import argparse
import multiprocessing
import subprocess
import os
import shutil
import timeit
import json
import string
import sys
if sys.version_info >= (3,11):
	import tomllib
else:
	raise Exception('Python 3.11 or later is required to run this script!')

"""
Summary of available subs:
 - game			- Path to game directory
 - bspfile		- BSP file name
 - bin			- Bin directory path
 - file			- Source file name (i.e. maps/test.vmf)
"""
configs = {
	'fast': {
		'steps': ['vbsp', 'vvis', 'vrad'],
		'vvis': '${bin}/vvis -game ${game} -fast ${bspfile}',
		'vrad': '${bin}/vrad -game ${game} -noao -StaticPropLighting -threads $threads -hdr -fast ${bspfile}',
		'vbsp': '${bin}/vbsp -game ${game} ${file}',
		'vbsp2': '${bin}/vbsp2 -game ${game} ${file}',
	},
	'normal': {
		'steps': ['vbsp', 'vvis', 'vrad'],
		'vvis': '${bin}/vvis -game ${game} ${bspfile}',
		'vrad': '${bin}/vrad -game ${game} -noao -textureshadows -StaticPropLighting -threads $threads -hdr ${bspfile}',
		'vbsp': '${bin}/vbsp -game ${game} ${file}',
		'vbsp2': '${bin}/vbsp2 -game ${game} ${file}',
	},
	'final': {
		'steps': ['vbsp', 'vvis', 'vrad'],
		'vvis': '${bin}/vvis -game ${game} ${bspfile}',
		'vrad': '${bin}/vrad -game ${game} -noao -final -textureshadows -StaticPropLighting -threads $threads -hdr -StaticPropPolys ${bspfile}',
		'vbsp': '${bin}/vbsp -game ${game} ${file}',
		'vbsp2': '${bin}/vbsp2 -game ${game} ${file}',
	}
}

profilers = {
	'vtune': '$vtune -collect hotspots $exe',
	'perf': 'perf record $exe'
}

argparser = argparse.ArgumentParser(description='Test harness for vrad, vvis, vbsp')
argparser.add_argument('--profile-vrad', action='store_true')
argparser.add_argument('--profile-vbsp', action='store_true')
argparser.add_argument('--profile-vvis', action='store_true')
argparser.add_argument('--profiler', type=str, choices=list(profilers.keys()))
argparser.add_argument('--show-graph', action='store_true')
argparser.add_argument('--threads', default=multiprocessing.cpu_count(), type=int, help='Number of threads to use. Defaults to half of your systems core count')
argparser.add_argument('--config', nargs='+', default=['normal'], help='Configs to use/compare')
argparser.add_argument('--game', type=str, default='p2ce', choices=['p2ce', 'momentum'], help='Games to compile for')
argparser.add_argument('--bench', action='store_true', help='Benchmark the compilers')
argparser.add_argument('map', metavar='Map', type=str, nargs=1, help='Map to compile')
args = argparser.parse_args()

timers = []

# Dead simple timer class for recording elapsed times
class Timer:
	def __init__(self, config: str):
		self.configname = config
		self.times = {}

	def begin_record(self, name):
		self.curname = name
		self.curstart = timeit.default_timer()

	def end_record(self):
		self.times[self.curname] = timeit.default_timer() - self.curstart


def check_result(result: subprocess.CompletedProcess):
	if result.returncode != 0:
		print('\e[93mERROR: Compile FAILED!\n\e[0m')
		exit(1)


def get_bin_directory() -> str:
	plat = 'linux64' if sys.platform.startswith('linux') else 'win64'
	return os.path.abspath(os.path.dirname(__file__) + f'../../../bin/{plat}')


def do_replacements(sourcemappath: str, bspfile: str, cmd: str) -> str:
	template = string.Template(cmd)
	return template.substitute({
		'game': args.game,
		'bspfile': bspfile,
		'file': sourcemappath,
		'threads': str(args.threads),
		'bin': get_bin_directory()
	})


# Find config by walking up the tree until we find a maps directory
def find_config(mapname: str) -> str|None:
	dir = os.path.dirname(os.path.abspath(mapname) if not os.path.isabs(mapname) else mapname)
	while not os.path.exists(f'{dir}/mapconfig.toml'):
		if os.path.exists(f'{dir}/maps') or dir == '/' or len(dir) == 0:
			return None
		dir = os.path.dirname(dir)
	return f'{dir}/mapconfig.toml'


def load_config(config: str|None) -> dict|None:
	if config is None:
		return None
	with open(config, 'rb') as fp:
		return tomllib.load(fp)


def inject_profiler():
	p = profilers[args.profiler]
	for k in configs.keys():
		if args.profile_vvis:
			configs[k]['vvis'] = p.replace('$exe', configs[k]['vvis'])
		if args.profile_vrad:
			configs[k]['vrad'] = p.replace('$exe', configs[k]['vrad'])
		if args.profile_vbsp:
			configs[k]['vbsp'] = p.replace('$exe', configs[k]['vbsp'])
			configs[k]['vbsp2'] = p.replace('$exe', configs[k]['vbsp2'])


def run_config(mapfile: str, config: str, dir: str):
	# This needs to be absolute. The engine makes some nasty assumptions about where compilers are run from
	if not os.path.isabs(mapfile):
		mapfile = os.path.abspath(os.path.join(dir, mapfile))
	
	# Find and load the toml, if it exists
	cfile = load_config(find_config(mapfile))
	if cfile is not None and config in cfile:
		cfg = cfile[config]
	else:
		cfg = configs[config]

	bspfile = mapfile.replace('.vmf', '.bsp')
	isbsp = mapfile.endswith('.bsp')
	mapname = os.path.basename(bspfile)
	
	timer = Timer(config)
	
	for step in cfg['steps']:
		timer.begin_record(step)
		r = subprocess.run(do_replacements(mapfile, bspfile, cfg[step]), shell=True)
		assert r.returncode == 0
		timer.end_record()

	timers.append(timer)


def output_results(timers: list[Timer]):
	outs = {}
	outs['configs'] = configs
	outs['results'] = {}
	for t in timers:
		outs['results'][t.configname] = t.times
	# Find appropriate file to write to
	p = 'results.json'
	i = 1
	while os.path.exists(p):
		p = f'results{i}.json'
		i += 1
	with open(p, 'w') as fp:
		json.dump(outs, fp)


def main():
	cwd = os.getcwd()
	
	os.chdir(os.path.dirname(__file__) + '/../../')

	# Sanity checks..
	if args.profiler == 'perf' and os.name == 'win32':
		print('ERROR: perf is not supported on Windows!')
		exit(1)
	
	# Set vtune path
	vtune_path = os.getenv('VTUNE')
	if vtune_path is not None:
		profilers['vtune'] = profilers['vtune'].replace('$vtune', vtune_path)
	elif os.name == 'win32' and args.profiler == 'vtune':
		print('ERROR: VTUNE environment variable must point to vtune.exe!')
		exit(1)
	else:
		profilers['vtune'] = profilers['vtune'].replace('$vtune', '/opt/intel/oneapi/vtune/latest/bin64/vtune') # Should pretty much always be installed here
	
	# Now run!
	if args.profiler is not None:
		inject_profiler()
	for c in args.config:
		run_config(args.map[0], c, cwd)
	
	# Post build results
	if args.bench:
		output_results(timers)


if __name__ == '__main__':
	main()
