#!/usr/bin/env python3

import argparse
import multiprocessing
import subprocess
import os
import shutil
import timeit
import json

argparser = argparse.ArgumentParser(description='Test harness for vrad, vvis, vbsp')
argparser.add_argument('--profile-vrad', action='store_true')
argparser.add_argument('--profile-vbsp', action='store_true')
argparser.add_argument('--profile-vvis', action='store_true')
argparser.add_argument('--profiler', type=str, choices=['vtune', 'perf'])
argparser.add_argument('--skip-vvis', action='store_true')
argparser.add_argument('--vbsp2', action='store_true')
argparser.add_argument('--skip-vbsp', action='store_true')
argparser.add_argument('--skip-vrad', action='store_true')
argparser.add_argument('--show-graph', action='store_true')
argparser.add_argument('--threads', default=-1, type=int, help='Number of threads to use. Defaults to half of your systems core count')
argparser.add_argument('--config', nargs='+', default=['fast'], help='Configs to use/compare')
argparser.add_argument('--game', type=str, default='p2ce', choices=['p2ce', 'momentum'], help='Games to compile for')
argparser.add_argument('--bench', action='store_true', help='Benchmark the compilers')
argparser.add_argument('map', metavar='Map', type=str, nargs=1, help='Map to compile')
args = argparser.parse_args()

configs = {
	'fast': {
		'vvis': './bin/linux64/vvis -game $game -fast $bspfile',
		'vrad': './bin/linux64/vrad -game $game -noao -StaticPropLighting -threads $threads -hdr -fast $bspfile',
		'vbsp': './bin/linux64/vbsp -game $game $file',
		'vbsp2': './bin/linux64/vbsp2 -game $game $file',
	},
	'normal': {
		'vvis': './bin/linux64/vvis -game $game $bspfile',
		'vrad': './bin/linux64/vrad -game $game -noao -textureshadows -StaticPropLighting -threads $threads -hdr $bspfile',
		'vbsp': './bin/linux64/vbsp -game $game $file',
		'vbsp2': './bin/linux64/vbsp2 -game $game $file',
	},
	'final': {
		'vvis': './bin/linux64/vvis -game $game $bspfile',
		'vrad': './bin/linux64/vrad -game $game -noao -final -textureshadows -StaticPropLighting -threads $threads -hdr -StaticPropPolys $bspfile',
		'vbsp': './bin/linux64/vbsp -game $game $file',
		'vbsp2': './bin/linux64/vbsp2 -game $game $file',
	}
}

VTUNE_PATH="$vtune -collect hotspots $exe"
PERF_PATH="perf record $exe"
timers = []
threads = multiprocessing.cpu_count() / 2

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

def do_replacements(sourcemappath: str, bspfile: str, cmd: str) -> str:
	global threads
	return cmd.replace('$game', args.game).replace('$bspfile', bspfile).replace('$file', sourcemappath).replace('$threads', str(threads))
	
def inject_profiler():
	p = VTUNE_PATH if args.profiler == 'vtune' else PERF_PATH
	for k in configs.keys():
		if args.profile_vvis:
			configs[k]['vvis'] = p.replace('$exe', configs[k]['vvis'])
		if args.profile_vrad:
			configs[k]['vrad'] = p.replace('$exe', configs[k]['vrad'])
		if args.profile_vbsp:
			configs[k]['vbsp'] = p.replace('$exe', configs[k]['vbsp'])
			configs[k]['vbsp2'] = p.replace('$exe', configs[k]['vbsp2'])

def run_config(mapfile: str, config: str):
	cfg = configs[config]
	bspfile = mapfile.replace('.vmf', '.bsp')
	isbsp = mapfile.endswith('.bsp')
	mapname = os.path.basename(bspfile)
	
	timer = Timer(config)
	
	# Skip vbsp if we're already a bsp
	if isbsp:
		args.skip_vbsp = True
	
	if not args.skip_vbsp:
		if args.vbsp2:
			timer.begin_record('vbsp2')
			r = subprocess.run(do_replacements(mapfile, bspfile, cfg['vbsp2']), shell=True)
			assert r.returncode == 0
			timer.end_record()
		else:
			timer.begin_record('vbsp')
			r = subprocess.run(do_replacements(mapfile, bspfile, cfg['vbsp']), shell=True)
			assert r.returncode == 0
			timer.end_record()
	if not args.skip_vvis:
		timer.begin_record('vvis')
		r = subprocess.run(do_replacements(mapfile, bspfile, cfg['vvis']), shell=True)
		assert r.returncode == 0
		timer.end_record()
	if not args.skip_vrad:
		timer.begin_record('vrad')
		r = subprocess.run(do_replacements(mapfile, bspfile, cfg['vrad']), shell=True)
		assert r.returncode == 0
		timer.end_record()

	# Copy the file into game
	try:
		shutil.copy(bspfile, f'{args.game}/maps/{mapname}')
	except shutil.SameFileError:
		pass # Eat it
	
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
	global VTUNE_PATH
	
	# Expected to be in sdk_tools/dev
	os.chdir(os.path.dirname(__file__) + '/../../')
	
	# Sanity checks..
	if args.profiler == 'perf' and os.name == 'win32':
		print('ERROR: perf is not supported on Windows!')
		exit(1)
	
	# Set vtune path
	vtune_path = os.getenv('VTUNE')
	if vtune_path is not None:
		VTUNE_PATH = VTUNE_PATH.replace('$vtune', vtune_path)
	elif os.name == 'win32' and args.profiler == 'vtune':
		print('ERROR: VTUNE environment variable must point to vtune.exe!')
		exit(1)
	else:
		VTUNE_PATH = VTUNE_PATH.replace('$vtune', '/opt/intel/oneapi/vtune/latest/bin64/vtune')
	
	# Now run!
	inject_profiler()
	for c in args.config:
		run_config(args.map[0], c)
	
	# Post build results
	if args.bench:
		output_results(timers)

if __name__ == '__main__':
	main()
