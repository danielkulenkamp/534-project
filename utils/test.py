import matplotlib.pyplot as plt
import numpy as np
import networkx as nx

import sys
import os
import argparse
from glob import glob
import re
import itertools
from distutils.util import strtobool

from multiprocessing import Pool


def get_graphs(node_dir):
    # Create a dictionary that maps IP addresses to testbed node names
    ip_to_node = {}
    for path in glob('{}/*/192.168.0.1'.format(node_dir)):
        node = path.split('/')[-2]

        found = False
        for line in open(path):
            if re.search('PING', line):
                found = True
                ip_to_node[line.split()[4]] = node
                break
        assert found, "Can't find IP address for node {}".format(node)
    assert len(ip_to_node) != 0, "Didn't find any nodes"

    # Graph G100 has edges between all 100% transmission probability links
    G100 = nx.DiGraph()
    # Graph Gall has edges between all non-zero transmission probability links
    Gall = nx.DiGraph()

    # Add edges to graphs
    for path in glob('{}/*/192.*'.format(node_dir)):
        to_node = from_node = packet_loss = None

        for line in open(path):
            parts = line.split()

            if re.search('PING', line):
                assert to_node is None and from_node is None, \
                        'More than one line with "PING" in it?'
                to_node = ip_to_node[parts[1]]
                from_node = ip_to_node[parts[4]]

            if re.search('packet loss', line):
                for i in xrange(len(parts)):
                    if parts[i] == 'packet':
                        assert packet_loss is None, \
                                'More than one line with "packet loss" in it?'
                        assert parts[i + 1] == 'loss,', \
                                'Packet loss not where expected in line'
                        packet_loss = float(parts[i - 1].strip('%'))/100.0

        assert to_node is not None and from_node is not None, \
                "Didn't find both to and from nodes"
        assert packet_loss is not None, "Didn't find packet loss"
        assert not(packet_loss < 0.0) and not(packet_loss > 1.0), \
                'Packet loss out of range: {}'.format(packet_loss)
        transmission_prob = 1 - packet_loss
        if transmission_prob == 1.0:
            G100.add_edge(from_node, to_node)
        if transmission_prob > 0.0:
            Gall.add_edge(from_node, to_node)

    for n1, n2 in G100.edges():
        assert Gall.has_edge(n1, n2), \
                'Sanity check failed, all edges in G100 should be in Gall'

    return G100, Gall


def find_five_complete(node_dir, plot=False):
    if isinstance(plot, basestring):
        plot = bool(strtobool(plot))

    G100, Gall = get_graphs(node_dir)

    p = Pool(12)
    p.map(process_perm, itertools.permutations(G100, 4))



def process_perm(nodes):
    complete = True
    global G100
    def has_edge(G, n1, n2):
        return G.has_edge(n1, n2) and G.has_edge(n2, n1)

    for i in range(4):
        if not(has_edge(G100, nodes[i], nodes[1])) or \
            not(has_edge(G100, nodes[i], nodes[2])) or \
            not(has_edge(G100, nodes[i], nodes[3])):
            complete = False

    if complete:
        print nodes


if __name__ == '__main__':
    node_dir = '/Users/danielkulenkamp/Documents/asu/honors_thesis/data/graph/000'

    G100, Gall = get_graphs(node_dir)

    p = Pool(12)
    p.map(process_perm, itertools.permutations(G100, 4))
