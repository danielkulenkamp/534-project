from __future__ import print_function
import sys
import os
import time

def update_node_file(num):
    with open('/users/dkulenka/repo/node_info.txt', 'r') as f:
        data = f.readlines()

        print(data)

    for i in xrange(len(data)):
        if data[i].startswith('#') and i < num:
            data[i] = data[i][1:]
    
    print(data)
    with open('/users/dkulenka/repo/node_info.txt', 'w') as f:
        f.writelines(data)

def run_exp_multi_newest(num_nodes):
        update_node_file(num_nodes)
        os.system('fab --password=backflip18 setup')
        os.system('fab --password=backflip18 setup_multihop')
        os.system('fab --password=backflip18 multi_newest')

if len(sys.argv) < 2:
        print("usage: python run_exps.py <num_nodes>")
else: 
        run_exp_multi_newest(int(sys.argv[1]))
