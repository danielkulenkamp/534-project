import sys
import os

import matplotlib
# matplotlib.rcParams['backend'] = "Qt4Agg"
import matplotlib.pyplot as plt
import numpy as np

# from fpdf import FPDF

def usage():
    print('usage: python newest_data.py <run_folder> <node_name> <num_runs>') 
    sys.exit(-1)


# drop rate; jitter; latency; MOS

def get_stats(file):
    with open(file) as f:
        lines = f.readlines()

    lines = lines[1:]
    
    # for line in lines:
    #     x = line.split()[0]
    #     print(x)
    #     sys.exit(-1)
    drop_rate = [float(line.split()[0]) for line in lines]
    jitter = [float(line.split()[1]) for line in lines]
    latency = [float(line.split()[2]) for line in lines]
    mos = [float(line.split()[3]) for line in lines]

    return drop_rate, jitter, latency, mos

def plot_stat(stat, stat_name, plot_name, x_axis, y_axis, ymin, ymax):
    _stat = [float(x) for x in stat]

    fig = plt.figure()
    plt.plot(_stat)
    #fig.suptitle('{}'.format(plot_name, fontsize=20))
    plt.ylabel(y_axis, fontsize=16)
    plt.xlabel(x_axis, fontsize=16)
    axes = plt.gca()
    axes.set_ylim([ymin,ymax])
    fig.savefig('{}.png'.format(stat_name))
    plt.close()

def average_runs(exp_folder, node, num_runs):
    runs = []
    if os.path.exists(exp_folder):
        for run in os.listdir(exp_folder):
            run_folder = os.path.join(exp_folder, run)
            node_folder = os.path.join(run_folder, node)
            
            for file in os.listdir(node_folder):
                if file.endswith('.txt'):
                    d, j, l, m = get_stats(os.path.join(node_folder, file))
                    runs.append([d, j, l, m])

    drop_rate = runs[0][0]
    jitter = runs[0][1]
    latency = runs[0][2]
    mos = runs[0][3]

    stats = runs[0]

    for i in range(1,num_runs):
        for j in range(0,num_runs):
            stats[j] = [x + y for x, y in zip(stats[j], runs[i][j])]
            
    
    for i in range(0,num_runs):
        stats[i] = [x / 4.0 for x in stats[i]]


    return stats

def plot_all(exp_folder, node, num_runs):
    avg_stats = average_runs(exp_folder, node, num_runs)

    stats_output = []
    stats_output.append('drop rate\n')
    stats_output.append('mean: {}\n'.format(np.mean(avg_stats[0])))
    stats_output.append('variance: {}\n'.format(np.var(avg_stats[0])))
    stats_output.append('std deviation: {}\n'.format(np.std(avg_stats[0])))

    stats_output.append('jitter\n')
    stats_output.append('mean: {}\n'.format(np.mean(avg_stats[1])))
    stats_output.append('variance: {}\n'.format(np.var(avg_stats[1])))
    stats_output.append('std deviation: {}\n'.format(np.std(avg_stats[1])))

    stats_output.append('delay\n')
    stats_output.append('mean: {}\n'.format(np.mean(avg_stats[2])))
    stats_output.append('variance: {}\n'.format(np.var(avg_stats[2])))
    stats_output.append('std deviation: {}\n'.format(np.std(avg_stats[2])))

    stats_output.append('mos\n')
    stats_output.append('mean: {}\n'.format(np.mean(avg_stats[3])))
    stats_output.append('variance: {}\n'.format(np.var(avg_stats[3])))
    stats_output.append('std deviation: {}\n'.format(np.std(avg_stats[3])))

    plot_stat(avg_stats[0], '{}/drop_rate'.format(exp_folder), 'Drop Rate', 'Time (seconds)', 'Percent dropped', -0.1, 1)
    plot_stat(avg_stats[1], '{}/jitter'.format(exp_folder), 'Jitter', 'Time (seconds)', 'Jitter', 0, 0.15)
    plot_stat(avg_stats[2], '{}/latency'.format(exp_folder), 'Latency', 'Time (seconds)', 'Delay (seconds)', 0, 0.5)
    plot_stat(avg_stats[3], '{}/mos'.format(exp_folder), 'Mean Opinion Score', 'Time (seconds)', 'MOS Score', 3, 4.5)

    with open('{}/stats.txt'.format(exp_folder), 'w') as f:
        f.writelines(stats_output)


# d, j, l, m = get_stats('/Users/danielkulenkamp/Documents/asu/honors_thesis/data/final/hidden/hidden_term/802/000/zotacI3/192.168.0.3.txt')


# avg = average_runs('/Users/danielkulenkamp/Documents/asu/honors_thesis/data/final/hidden/hidden_term/react/', 'zotacI3')

if len(sys.argv) < 3:
    usage()

plot_all(sys.argv[1], sys.argv[2], int(sys.argv[3]))



