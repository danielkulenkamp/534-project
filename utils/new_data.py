import sys
import os
import statistics
import csv
from pathlib import Path

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

def get_folders(root_folder):
    if os.path.exists(root_folder):
        for exp_num in os.listdir(root_folder):
            subdir = os.path.join(root_folder, exp_num)
            for exp in os.listdir(subdir):
                full_path = os.path.join(subdir, exp)
                if os.path.isdir(full_path):
                    yield full_path


def make_folders(root_folder):
    for full_path in get_folders(root_folder):
        if not os.path.exists('{}/plots'.format(full_path)):
            os.makedirs('{}/plots'.format(full_path))
            os.makedirs('{}/plots/jitter'.format(full_path))
            os.makedirs('{}/plots/delay'.format(full_path))
            os.makedirs('{}/plots/loss'.format(full_path))
            os.makedirs('{}/plots/load'.format(full_path))


def plot(root_folder):

    def plot_stat(exp_folder, data, stat, x_axis, y_axis):
        global image_list

        _data = [x for x in data[STATS[stat]] if x != 'N/A']

        _data = [float(x) for x in _data]

        # y_max = max(max(_802), max(react))
        # y_min = min(min(_802), min(react))

        fig = plt.figure()
        plt.plot(_data)
        fig.suptitle('{}'.format('Throughput' if stat == 'load' else stat.title()), fontsize=20)
        plt.xlabel(x_axis, fontsize=16)
        plt.ylabel(y_axis, fontsize = 16)
        axes = plt.gca()
        # axes.set_ylim([y_min, y_max])

        fig_name = '{}/{}.png'.format(exp_folder, 'throughput' if stat == 'load' else stat)

        fig.savefig(fig_name)
        image_list.append(fig_name)

        plt.close()

    def get_title(image):
        return image.split('/')[9]

    def makepdf(location):
        pdf = FPDF()
        counter = 0
        pdf.add_page()
        pdf.set_font('Arial', '', 16)
        pdf.cell(50, 10, 'Testbed Results', 1)
        pdf.add_page()
        image_list.sort()

        new_list = []

        new_list = image_list

        # In this case, we are only doing one set of tests, using TCP and UDP we are using RTP. So the pattern to sort it is different.

        # This code is for when there are tests for both UDP and TCP, but that doesn't apply when I am using my streaming code. 
        # a = 0
        # while a < len(image_list):
        #     new_list.append(image_list[a])
        #     a += 1
        #     new_list.append(image_list[a])
        #     a += 1
        #     new_list.append(image_list[a])
        #     a += 1 
        #     new_list.append(image_list[a])
        #     a += 5

        #     new_list.append(image_list[a])
        #     a += 1
        #     new_list.append(image_list[a])
        #     a += 1
        #     new_list.append(image_list[a])
        #     a += 1
        #     new_list.append(image_list[a])
        #     a -= 7

        #     new_list.append(image_list[a])
        #     a += 1
        #     new_list.append(image_list[a])
        #     a += 1
        #     new_list.append(image_list[a])
        #     a += 1
        #     new_list.append(image_list[a])
        #     a += 5

        #     new_list.append(image_list[a])
        #     a += 1
        #     new_list.append(image_list[a])
        #     a += 1
        #     new_list.append(image_list[a])
        #     a += 1
        #     new_list.append(image_list[a])
        #     a += 1

        for image in new_list:
            print('Adding image: {}'.format(image)) 
            if counter == 4:
                pdf.add_page()
                counter = 0

            if counter == 0:
                pdf.cell(50, 10, '{}'.format(get_title(image)), 1)
                pdf.image(image,10,70,80,60)
            elif counter == 1:
                pdf.image(image, 110, 70, 80, 60)
            elif counter == 2:
                pdf.image(image, 10, 170, 80, 60)
            elif counter == 3: 
                pdf.image(image, 110, 170, 80, 60)

            counter += 1

        pdf.output('{}/charts.pdf'.format(location), 'F')

    for exp_path in get_folders(root_folder):
        data_filepath = '{}/zotacD1/averages_testmeas.txt'.format(exp_path)
        print('Doing image: {}'.format(data_filepath))

        try:
            data_stats = get_stats(data_filepath)
        except:
            print('file not found: {}'.format(data_filepath))
            print('continuing to next file')

        for stat in STATS.keys():
            plot_stat('{}/plots/{}'.format(exp_path, stat), data_stats, stat, 'Time [s]', STATS[stat][3:].capitalize())

    print('Making PDF')
    makepdf(root_folder)

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


def average_stat(data, stat):
    _data = [x for x in data[STATS[stat]] if x != 'N/A']

    _data = [float(x) for x in _data]

    average = statistics.mean(_data)
    return average

def get_averages_for_file(file):
    stats = get_stats(file)
    
    averages = []
    for stat in STATS.keys():
        averages.append(average_stat(stats, stat))

    return averages

def extract_averages(runs_folder):
    if os.path.exists(runs_folder):
        output_filepath = os.path.join(runs_folder, 'output.txt')

        file_contents = []
        with open(output_filepath, 'w') as f:
            f.write('delay,jitter,loss,load\n')
            for run in os.listdir(runs_folder):
                if not run.startswith('run'):
                    continue
                filepath = os.path.join(runs_folder, "{}/000/zotacI6/averages_testmeas.txt".format(run))
                stats = get_stats(filepath)
                averages = get_averages_for_file(filepath)
                file_contents.append(averages)
                s = ''
                for av in averages:
                    s += '{},'.format(av)
                s = s.rstrip(',')
                s += '\n'
                print(s)
                f.write(s)

def combine_averages(files):
    exps = []
    for file in files:
        with open(file) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')

            temp = []
            for line in csv_reader:
                if line[0] != 'delay':
                    temp.append([float(x) for x in line])
            
            exps.append(temp)

    averaged = np.mean(np.array(exps), axis=0)     

    return averaged

if len(sys.argv) == 1:
    usage()

# for file in sys.argv[1:]:
#     extract_averages(file)

output_files = ['{}/output.txt'.format(file) for file in sys.argv[1:]]
averaged = combine_averages(output_files)

path = Path(sys.argv[1]).parent

with open(os.path.join(path, 'delay.txt'), 'w') as f:
    f.write('147\n')
    f.write('Delay\n')
    for line in averaged:
        f.write('{}\n'.format(line[0]))

with open(os.path.join(path, 'combined.tsv'), 'w') as f:
    f.write('147\t\n')
    f.write('Delay\tJitter\tLoss\tThroughput\n')
    for line in averaged:
        f.write('{}\t{}\t{}\t{}\n'.format(round(line[0],5), round(line[1],5), round(line[2],5), round(line[3],5)))

with open(os.path.join(path, 'combined.csv'), 'w') as f:
    f.write('Delay,Jitter,Loss,Throughput\n')
    for line in averaged:
        f.write('{},{},{},{}\n'.format(round(line[0],5), round(line[1],5), round(line[2],5), round(line[3],5)))



# extract_averages(sys.argv[2])
# extract_averages(sys.argv[3])



# avgs = get_averages_for_file(sys.argv[1])

# for av in avgs:
#     print(av)

# stats = get_stats(sys.argv[1])

# average = average_stat(stats, 'delay')
# print(average)
# foldername = sys.argv[1]

# make_folders(foldername)

# plot(foldername)

