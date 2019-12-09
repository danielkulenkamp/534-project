import sys
import os

import matplotlib
matplotlib.rcParams['backend'] = "Qt4Agg"
import matplotlib.pyplot as plt
import numpy as np

def usage():
    print("usage: python qos_data.py <data_folder>")
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


def make_folders(root_folder):
    if os.path.exists(root_folder):
        if not os.path.exists('{}/plots'.format(root_folder)):
            os.makedirs('{}/plots'.format(root_folder))
            os.makedirs('{}/plots/1hop/jitter'.format(root_folder))
            os.makedirs('{}/plots/1hop/delay'.format(root_folder))
            os.makedirs('{}/plots/1hop/loss'.format(root_folder))
            os.makedirs('{}/plots/1hop/load'.format(root_folder))
            os.makedirs('{}/plots/2hop/jitter'.format(root_folder))
            os.makedirs('{}/plots/2hop/delay'.format(root_folder))
            os.makedirs('{}/plots/2hop/loss'.format(root_folder))
            os.makedirs('{}/plots/2hop/load'.format(root_folder))
            os.makedirs('{}/plots/3hop/jitter'.format(root_folder))
            os.makedirs('{}/plots/3hop/delay'.format(root_folder))
            os.makedirs('{}/plots/3hop/loss'.format(root_folder))
            os.makedirs('{}/plots/3hop/load'.format(root_folder))
            os.makedirs('{}/plots/4hop/jitter'.format(root_folder))
            os.makedirs('{}/plots/4hop/delay'.format(root_folder))
            os.makedirs('{}/plots/4hop/loss'.format(root_folder))
            os.makedirs('{}/plots/4hop/load'.format(root_folder))



    else:
        usage()

def plot(root_folder):
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

    def plot_stat(hop_folder, data_react, data_802, stat, x_axis, y_axis):
        _802 = [x for x in data_802[STATS[stat]] if x != 'N/A']
        _802 = [float(x) for x in _802]

        react = [x for x in data_react[STATS[stat]] if x != 'N/A']
        react = [float(x) for x in react]

        y_max = max(max(_802), max(react))
        y_min = min(min(_802), min(react))

        fig = plt.figure()
        plt.plot(_802)
        #fig.suptitle('{}: 802.11'.format('Throughput' if stat == 'load' else stat.title()), fontsize=20)
        plt.xlabel(x_axis, fontsize=16)
        plt.ylabel(y_axis, fontsize = 16)
        axes = plt.gca()
        axes.set_ylim([y_min, y_max])

        fig.savefig('{}/{}_802.png'.format(hop_folder, 'throughput' if stat == 'load' else stat))
        plt.close()

        fig = plt.figure()
        plt.plot(react)
        #fig.suptitle('{}: REACT'.format('Throughput' if stat == 'load' else stat.title()), fontsize=20)
        plt.xlabel(x_axis, fontsize=16)
        plt.ylabel(y_axis, fontsize = 16)
        axes = plt.gca()
        axes.set_ylim([y_min, y_max])

        fig.savefig('{}/{}_react.png'.format(hop_folder, 'throughput' if stat == 'load' else stat))
        plt.close()


    folders = os.listdir(root_folder)
    
    for folder in folders:
        if folder == '1hop' or folder == '2hop' or \
           folder == '3hop' or folder == '4hop':
            print("YAY")
            data_filepath_802 = '{}/{}/3-802-tcp/zotacI6/averages_testmeas.txt'.format(root_folder,folder)
            data_filepath_react = '{}/{}/3-react-tcp/zotacI6/averages_testmeas.txt'.format(root_folder,folder)

            # extract stats from files
            stats_802 = get_stats(data_filepath_802)
            stats_react = get_stats(data_filepath_react)

            for stat in STATS.keys(): 
                plot_stat('{}/plots/{}/{}'.format(root_folder, folder, stat), stats_react, stats_802, stat, 'Time [s]', STATS[stat][3:].capitalize())




if len(sys.argv) == 1:
    usage()

foldername = sys.argv[1]

make_folders(foldername)

plot(foldername)

usage()

lines = []

with open(filename) as f:
    lines = f.readlines()

for i in range(13):
    lines.pop(0)


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

"""
So I need to extract the following: 
DL delay [ms]
DL jitter (abs.) [ms] or (MA)
DL Total Pkt loss
DL Load [kb/s]
"""


delay = [x for x in stats['DL delay [ms]'] if x != 'N/A']
jitter = [x for x in stats['DL jitter (abs.) [ms]'] if x != 'N/A']
loss = [x for x in stats['DL Total Pkt loss'] if x != 'N/A']
load = [x for x in stats['DL Load [kb/s]'] if x != 'N/A']


delay = [float(x) for x in delay]
jitter = [float(x) for x in jitter]
loss = [float(x) for x in loss]
load = [float(x) for x in load]

fig_delay = plt.figure()
plt.plot(delay)
fig_delay.suptitle('Delay', fontsize=20)
plt.xlabel('Samples', fontsize=18)
plt.ylabel('Delay [ms]', fontsize=16)
max_ = max(delay)
min_ = min(delay)
axes = plt.gca()
axes.set_ylim([min_-100,max_+100])
fig_delay.savefig('delay.png')

fig_jitter = plt.figure()
plt.plot(jitter)


print(delay)
print(jitter)
print(loss)
print(load)







