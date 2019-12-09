import os
import time
import subprocess
import sys

node = '' 
if len(sys.argv) == 1:
    print 'usage: python check_clocks.py <node_name>'
    sys.exit(0)
else: 
    node = sys.argv[1]


clocks_synced = False
accuracy_ms = 1
iterations = 0
verif_len = 10


def check_clocks(n):
    output = subprocess.check_output('clockdiff {}'.format(n), shell=True)

    return int(output.split('\n')[0].split(' ')[2])

while not clocks_synced:
    zotac = check_clocks(node)
    if abs(zotac) <= accuracy_ms:
        correct_attempts = 0
        while correct_attempts < verif_len:
            zotac = check_clocks(node)
            if abs(zotac) <= accuracy_ms:
                correct_attempts += 1
            
            if correct_attempts > verif_len:
                print 'CLOCKS SYNCHRONIZED - Accuracy threshold: {}'.format(accuracy_ms)
                clocks_synced = True

    else:
        print 'NOT SYNCHRONIZED - Accuracy threshold: {}'.format(accuracy_ms)

    print '{}: {}'.format(node, zotac)
    print '-'*40
    time.sleep(5)
    iterations += 1



    


