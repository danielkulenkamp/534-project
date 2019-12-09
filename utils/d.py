import sys
import os

import matplotlib
matplotlib.rcParams['backend'] = "Qt4Agg"
import matplotlib.pyplot as plt
import numpy as np

from fpdf import FPDF

def usage():
    print('usage: python new_data.py <path_to_multi_newest>')
    sys.exit(0)

DELAY = 'DL delay [ms]'
JITTER = 'DL jitter (abs.) [ms]'
LOSS = 'DL Total Pkt loss'
LOAD = 'DL Load [kb/s]'

STATS = {
'delay': DELAY,
'jitter': JITTER,
'loss': LOSS,
'load': LOAD
}

image_list = []

def get_stats(file):
    lines = []
    with open(file) as f:
        lines = f.readlines()
    for i in range(13):
        lines.pop(0)

    # not currently used, just for reference
    start_time = lines.pop(0)[24:]

    for i in range(3):
        lines.pop(0)
    
    stat_names = lines.pop(0).split('\t')

    stats = {}

    for stat in stat_names:
        stats[stat] = []

    lines.pop(0)

    num_stats = len(stat_names)

    for line in lines:
        stat_name_count = 0

        split_data = line.split('\t')

        while stat_name_count < num_stats:
            stats[stat_names[stat_name_count]].append(split_data[stat_name_count])
            stat_name_count += 1

    stats.pop('\n', None)
    
    return stats

stats = get_stats('/Users/danielkulenkamp/Documents/asu/honors_thesis/data/7-23-19/002/2-802-iperf_low/zotacK2/averages_testmeas.txt')

throughput = [x for x in stats[STATS['load']] if x != 'N/A']
throughput = [float(x) for x in throughput]

print(throughput)