#!/usr/bin/env python3

# Totally garbage script to graph map compile results
import json
import typing
import matplotlib.pyplot as plt
import argparse
import numpy as np

argparser = argparse.ArgumentParser()
argparser.add_argument('results', metavar='results', type=str, help='Results file to use')
argparser.add_argument('--exclude-vvis', action='store_true', help='Dont plot vvis')
argparser.add_argument('--exclude-vbsp', action='store_true', help='Dont plot vbsp')
argparser.add_argument('--exclude-vrad', action='store_true', help='Dont plot vrad')
argparser.add_argument('--exclude-vbsp2', action='store_true', help='Dont plot vbsp2')

args = argparser.parse_args()

def get_key(c: dict, k: str) -> typing.Any:
	try:
		return round(c[k],2)
	except:
		return None

def plot_results(res: dict):
	fig, xbars = plt.subplots()
	
	xbars.set_ylabel('Time (seconds)')
	xbars.set_xlabel('Configuration type')
	
	vrad = []
	vvis = []
	vbsp = []
	vbsp2 = []
	for config in res['results'].values():
		vrad.append(get_key(config, 'vrad'))
		vvis.append(get_key(config, 'vvis'))
		vbsp.append(get_key(config, 'vbsp'))
		vbsp2.append(get_key(config,'vbsp2'))
	
	graphs = {}
	if not args.exclude_vrad and len(vrad) != 0 and vrad[0] is not None:
		graphs['vrad'] = vrad
	if not args.exclude_vvis and len(vvis) != 0 and vvis[0] is not None:
		graphs['vvis'] = vvis
	if not args.exclude_vbsp and len(vbsp) != 0 and vbsp[0] is not None:
		graphs['vbsp'] = vbsp
	if not args.exclude_vbsp2 and len(vbsp2) != 0 and vbsp2[0] is not None:
		graphs['vbsp2'] = vbsp2
	
	numgraphs = len(graphs)
	cringe = 0
	for m in graphs.values():
		cringe = len(m)
		break
	barpos = np.arange(cringe)
	w = 0.5
	
	i = 0
	labels = []
	for k,g in graphs.items():
		inc = w / numgraphs
		l = None
		if numgraphs == 3:
			l = xbars.bar(barpos + inc*(i-1), g, w / numgraphs, label=k)
		elif numgraphs == 2:
			l = xbars.bar(barpos + (inc/2*i) + (inc/2*(i-1)), g, w / numgraphs, label=k)
		elif numgraphs == 1:
			l = xbars.bar(barpos, g, w, label=k)
		xbars.bar_label(l, padding=1)
		i+=1
	
	labels = []
	for k in res['results'].keys():
		labels.append(k)
	
	extent = numgraphs * cringe * w + w * 4
	xbars.set_xticks(barpos, labels)
	xbars.legend()
	xbars.set_xlim(-extent/2, extent/2)
	xbars.set_title('Compile tools performance comparison')
	fig.tight_layout()
	plt.show()

def main():
	with open(args.results, 'r') as fp:
		plot_results(json.load(fp))

if __name__ == '__main__':
	main()