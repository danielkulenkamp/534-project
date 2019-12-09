#!/usr/bin/env python2

import time
import os
import random
from distutils.util import strtobool
import json
import math
import random
import sys

import fabric.api as fab
from fabric.contrib.files import exists
from fabric.operations import sudo
from fabric.context_managers import settings


from utils.conn_matrix import ConnMatrix
from utils.meas_matrix import MeasMatrix
from utils.username import get_username

fab.env.user = get_username()
project_path = os.path.join('/users', fab.env.user, 'react80211')

hosts_driver = []
hosts_txpower = []

def set_hosts(host_file):
    #fab.env.hosts = open(host_file, 'r').readlines()
    global hosts_txpower;
    hosts_info_file = open(host_file, 'r').readlines()
    hosts_info=[];
    hosts_driver=[];
    for i in hosts_info_file:
        if not i.startswith("#"):
            hosts_info.append(i);
    fab.env.hosts = [i.split(',')[0] for i in hosts_info]
    hosts_driver= [i.split(',')[1].replace("\n", "") for i in hosts_info]
    print hosts_driver
    hosts_txpower= [i.split(',')[2].replace("\n", "") for i in hosts_info]
    return hosts_driver

#---------------------
#SET NODES
hosts_driver = set_hosts('node_info.txt')

@fab.task
@fab.parallel
def install_python_deps():
    fab.sudo("apt-get install -y python-scapy python-netifaces python-numpy python-flask")
    fab.sudo('apt-get install iputils-clockdiff inetutils-traceroute')

@fab.task
@fab.parallel
# Ad-hoc node association
#echo "usage $0 <iface> <essid> <freq> <power> <rate> <ip> <mac> <reload[1|0]>"
def associate(driver,iface,essid,freq,txpower,rate,ip_addr,mac_address="aa:bb:cc:dd:ee:ff",skip_reload=False,rts='off'):
    # Load kernel modules
    fab.sudo('cd ~/backports-cw-tuning/ && ./load.sh')

    # Setup wireless interfaces
    with fab.settings(warn_only=True):
            fab.run('sudo iwconfig {0} mode ad-hoc; sudo ifconfig {0} {5} up;sudo iwconfig {0} txpower {3}dbm; sudo iwconfig {0} rate {4}M fixed;sudo iw dev {0} ibss join {1} {2} fixed-freq {6}'.format(iface,essid,freq,txpower,rate,ip_addr,mac_address))
            iface_mon='mon0';
            fab.sudo('iw dev {0} interface add {1} type monitor'.format(iface,iface_mon));
            fab.sudo('ifconfig {0} up'.format(iface_mon));
            fab.run('sudo iwconfig {0} rts {1}'.format(iface,rts))

@fab.task
@fab.parallel
def set_txpower(txpower):
    fab.run('sudo iwconfig wlan0 txpower {0}'.format(txpower))

@fab.task
#setup network, ad-hoc association
def network(freq=2412,host_file=''):
    global hosts_txpower

    #search my host
    i_ip=fab.env.hosts.index(fab.env.host)
    print fab.env.hosts
    print hosts_driver
    driver=hosts_driver[i_ip];
    txpower=hosts_txpower[i_ip]
    print hosts_txpower
    fab.execute(associate,driver,'wlan0','test',freq,txpower,6,'192.168.0.{0}'.format(i_ip+1),'aa:bb:cc:dd:ee:ff',skip_reload=False,rts='250',hosts=[fab.env.hosts[i_ip]])

@fab.task
@fab.parallel
def stop_react():
    screen_stop_session('react')

@fab.task
@fab.parallel
def stop_react2():
    with fab.settings(warn_only=True):
        fab.sudo("pid=$(pgrep react.py) && kill -9 $pid")


@fab.task
@fab.parallel
def try_react():
    stop_react()
    screen_start_session('react',
            'sudo python2.7 -u /users/dkulenka/react80211/_react.py -i wlan0 -t 0.1 -r 6000 -b 0.6 -k 500 -c 0.28 -p 0.26 -e new -o /users/dkulenka/repo/hi')


@fab.task
@fab.parallel
def run_react(out_dir=None, tuner='new', beta=0.6, k=500, capacity=80,
        prealloc=0):
    args = []

    args.append('-i')
    args.append('wlan0')

    args.append('-t')
    args.append('0.1')

    args.append('-r')
    args.append('6000')

    args.append('-b')
    args.append(str(beta))

    args.append('-k')
    args.append(str(k))

    args.append('-c')
    args.append(str(capacity))

    args.append('-p')
    args.append(str(prealloc))

    # Without a tuner REACT is disabled and we just collect airtime data
    if tuner == 'new' or tuner == 'old':
        print("YES ITS THERE")
        args.append('-e')
        args.append(tuner)

    args.append('-o')
    if out_dir is None:
        # Don't use unique output directory (this case is just for testing)
        out_dir = makeout(unique=False)
    args.append('{}/react.csv'.format(out_dir))

    stop_react()

    print(project_path)
    print(args)
    screen_start_session('react',
            'sudo python2.7 -u {}/_react.py {}'.format(project_path,
            ' '.join(args)))

@fab.task
@fab.parallel
def run_react2(out_dir=None, enable_react=True):
    args = []

    args.append('-i')
    args.append('wlan0')

    args.append('-t')
    args.append('0.1')

    args.append('-r')
    args.append('6000')

    if enable_react:
        args.append('-e')

    args.append('-o')
    if out_dir is None:
        out_dir = makeout()
    args.append(out_dir)

    stop_react2()
    fab.sudo('setsid {}/react.py {} &>~/react.{}.out </dev/null &'.format(
        project_path, ' '.join(args), fab.env.host), pty=False)

################################################################################
# misc

import socket
import struct

def dot2long(ip):
    return struct.unpack("!L", socket.inet_aton(ip))[0]

def long2dot(ip):
    return socket.inet_ntoa(struct.pack('!L', ip))

def get_my_mac(dev='wlan0'):
    cmd = 'python -c' \
            " 'from netifaces import *;" \
            ' print ifaddresses("{}")[17][0]["addr"]\''
    return fab.run(cmd.format(dev))

def get_my_ip(dev='wlan0'):
    cmd = 'python -c' \
            " 'from netifaces import *;" \
            ' print ifaddresses("{}")[AF_INET][0]["addr"]\''
    return fab.run(cmd.format(dev))

def get_foreign_ip(foreign_host, dev='eth0'):
    result = "" 
    with (settings(host_string=foreign_host, user='dkulenka')):
        cmd = 'python -c' \
            " 'from netifaces import *;" \
            ' print ifaddresses("{}")[AF_INET][0]["addr"]\''
        result = sudo(cmd.format(dev))

    return result    

@fab.task
@fab.parallel
def time_sync():
    fab.sudo('service ntp stop')
    fab.sudo('ntpdate time.nist.gov')

@fab.task
@fab.parallel
def rm_proxy():
    fab.sudo('rm -f /etc/apt/apt.conf.d/01proxy')

@fab.task
def ptpd():
    screen_start_session('ptpd', 'sudo ptpd -e -d -c -b eth0')
    time.sleep(3)
    # fab.sudo('ptpd -b eth0')
    # start ptpd
    # ip2mac = {}
    # fab.execute(collect_ip2mac_map, ip2mac)
    # last = None
    # for ip in ip2mac:
    #     if last is None or ip > last:
    #         last = ip
    # last = long2dot(last)

    # print('THIS IS THE LAST: {}'.format(last))
    # if get_my_ip() == '192.168.0.1':
    #     foreign = get_foreign_ip('{}'.format(last))
    #     time.sleep(10)
    #     fab.sudo('ptpd -b eth0 -u 10.11.16.29')
    # elif get_my_ip() == last:
    #     fab.sudo('ptpd -b eth0')


@fab.task
@fab.parallel
def yobooyathere():
    fab.run(':')

################################################################################
# screen

def screen_start_session(name, cmd):
    # p = os.popen('screen -ls | grep {}'.format(name))
    # output = p.read()
    # p.close()
    # if output == '':
    fab.run('screen -S {} -dm bash -c "{}"'.format(name, cmd), pty=False)

def screen_stop_session(name, interrupt=False):
    with fab.settings(warn_only=True):
        if interrupt:
            fab.run('screen -S {} -p 0 -X stuff ""'.format(name))
        else:
            fab.run('screen -S {} -X quit'.format(name))

def screen_run_command(name, command):
    with fab.settings(warn_only=True):
        fab.run("screen -S {} -p 0 -X stuff $'{}\015'".format(name, command))

def screen_stop_probes():
    with fab.settings(warn_only=True):
        fab.run("screen -ls | awk -vFS='\t|[.]' '/probe/ {system(\"screen -S \"$2\" -X quit\")}'")

def screen_stop_scopes():
    with fab.settings(warn_only=True):
        fab.run("screen -ls | awk -vFS='\t|[.]' '/scope/ {system(\"screen -S \"$2\" -X quit\")}'")

@fab.task
def screen_list():
    return fab.run('ls /var/run/screen/S-$(whoami)').split()

@fab.task
def screen_stop_all():
    with fab.settings(warn_only=True):
        fab.run('screen -wipe')

    sessions = screen_list()
    for name in sessions:
        if name.split('.')[1] != 'running' and name.split('.')[1] != 'ptpd':
            screen_stop_session(name)

@fab.task
def screen_wipe():
    with fab.settings(warn_only=True):
        fab.run('screen -wipe')

    sessions = screen_list()
    for name in sessions:
        screen_stop_session(name)


################################################################################
# iperf and roadtrip

@fab.task
def iperf_start_servers():
    screen_start_session('iperf_server_udp', 'iperf -s -u')
    screen_start_session('iperf_server_tcp', 'iperf -s')

@fab.task
def iperf_stop_servers():
    screen_stop_session('iperf_server_udp', 'iperf -s -u')
    screen_stop_session('iperf_server_tcp', 'iperf -s')

@fab.task
def iperf_start_clients(host_out_dir, conn_matrix, tcp=False, rate='1G'):
    for server in conn_matrix.links(get_my_ip()):
        cmd = 'iperf -c {}'.format(server)
        if not(tcp):
            cmd += ' -u -b {}'.format(rate)
        cmd += ' -t -1 -i 1 -yC'

        # Use -i (ignore signals) so that SIGINT propagted up pipe to iperf
        cmd += ' | tee -i {}/{}.csv'.format(host_out_dir, server)

        screen_start_session('iperf_client', cmd)

@fab.task
def iperf_stop_clients():
    screen_stop_session('iperf_client', interrupt=True)

@fab.task
def roadtrip_start_servers():
    # Roadtrip listens for TCP and UDP at the same time by default
    screen_start_session('roadtrip_server', '~/bin/roadtrip -listen' \
            ' &>>~/data/{}_roadtrip.log'.format(fab.env.host))

@fab.task
def roadtrip_start_clients(host_out_dir, conn_matrix, tcp=False):
    for server in conn_matrix.links(get_my_ip()):
        args = []

        args.append('-address')
        args.append(server)

        if not(tcp):
            args.append('-udp')

        cmd = '~/bin/roadtrip {} 2>&1 | tee -i {}/roadtrip_{}.csv'.format(
                " ".join(args), host_out_dir, server)

        screen_start_session('roadtrip_client', cmd)

@fab.task
def roadtrip_stop_clients():
    screen_stop_session('roadtrip_client', interrupt=True)

@fab.task 
def opus_start_receivers_new(host_out_dir, conn_matrix, last = None):
    cmd = '/users/dkulenka/opus_rtp_MOS/MOS_DGRAM -f wlan0 -a WIDE-BAND -o 4.75 -p 5000 | tee {}/{}.txt'.format(host_out_dir, get_my_ip())
    print cmd
    screen_start_session('opus_receiver', cmd)

@fab.task
def opus_start_receivers(host_out_dir, conn_matrix, last = None):
    # if last is not None:
    #     port = int(last.split('.')[3]) + 5000
    # else: 
    port = int(get_my_ip().split('.')[3]) + 5000
    print("MY IP: {}".format(get_my_ip()))
    cmd = '/users/dkulenka/opus_rtp_MOS/MOS_DGRAM -f wlan0 -g 224.0.0.1 -a WIDE-BAND -o 4.75 -p {} | tee {}/{}.txt'.format(port, host_out_dir, get_my_ip())
    screen_start_session('opus_receiver', cmd)

@fab.task
def opus_stop_receivers():
    screen_stop_session('opus_receiver', interrupt=True)

@fab.task
def opus_start_streamers_new(host_out_dir, conn_matrix):
    for server in conn_matrix.links(get_my_ip()):
        if server is not None:
            cmd = '/users/dkulenka/opus_rtp_MOS/rtp_opus_streamer -a {} -p 5000 -f /users/dkulenka/opus_rtp_MOS/new.wav -r 256000 | tee {}/{}.txt'.format(server, host_out_dir, server)

            screen_start_session('opus_streamer', cmd)

@fab.task
def opus_start_streamers(host_out_dir, conn_matrix):
    for server in conn_matrix.links(get_my_ip()):
        if server is not None: 
            port = int(server.split('.')[3])+5000
            print("MY IP: {}".format(get_my_ip()))
            
            cmd = '/users/dkulenka/opus_rtp_MOS/rtp_opus_streamer -a 224.0.0.1 -p {} -f /users/dkulenka/opus_rtp_MOS/new.wav -r 16000 | tee {}/{}.txt'.format(port, host_out_dir, server)
            #cmd += ' | tee -i {}/{}.csv'.format(host_out_dir, server)

            screen_start_session('opus_streamer', cmd)

@fab.task
def opus_stop_streamers():
    screen_stop_session('opus_streamer', interrupt=True)

################################################################################
# Multi-hop MAC address setup

def collect_ip2mac_map(ip2mac):
    ip2mac[dot2long(get_my_ip())] = get_my_mac()

def sudo_ip_neigh_add(ip, mac):
    if not(isinstance(ip, str)):
        ip = long2dot(ip)

    ip_neigh_add_cmd = 'ip neighbor add {} lladdr {} dev wlan0 nud permanent'
    fab.sudo(ip_neigh_add_cmd.format(ip, mac))

def set_neighbors(ip2mac):
    low_neigh = None
    myip = dot2long(get_my_ip())
    high_neigh = None

    lower = []
    higher = []

    for ip in ip2mac.keys():
        if ip + 1 == myip:
            low_neigh = ip
        elif ip - 1 == myip:
            high_neigh = ip
        elif ip < myip:
            lower.append(ip)
        elif ip > myip:
            higher.append(ip)
        else:
            pass # ip == myip

    fab.sudo('sysctl -w net.ipv4.ip_forward=1')
    fab.sudo('ip link set dev wlan0 arp off')
    fab.sudo('ip neigh flush dev wlan0')

    if low_neigh is not None:
        sudo_ip_neigh_add(low_neigh, ip2mac[low_neigh])
        for ip in lower:
            sudo_ip_neigh_add(ip, ip2mac[low_neigh])

    if high_neigh is not None:
        sudo_ip_neigh_add(high_neigh, ip2mac[high_neigh])
        for ip in higher:
            sudo_ip_neigh_add(ip, ip2mac[high_neigh])

def setup_multicast():
    fab.sudo('route add -net 224.0.0.0 netmask 240.0.0.0 dev wlan0')

@fab.task
@fab.runs_once
def setup_multihop():
    ip2mac = {}
    fab.execute(collect_ip2mac_map, ip2mac)
    fab.execute(set_neighbors, ip2mac)
    #fab.execute(setup_multicast)
    time.sleep(60)

################################################################################
# Multi-hop Reservations

@fab.parallel
def res_server_kickoff(ip2mac):

    def get_if_in_ip2mac(ip):
        if ip in ip2mac:
            return long2dot(ip)
        else:
            return ""

    myip = dot2long(get_my_ip())
    n1 = get_if_in_ip2mac(myip - 1)
    n2 = get_if_in_ip2mac(myip + 1)
    myip = long2dot(myip)

    screen_start_session('res_server',
            'python2.7 -u' \
            ' {}/reservation/reservation_server.py {} {} {}' \
            ' &>>~/data/{}_res_server.log'.format(project_path, myip, n1, n2,
            fab.env.host))

@fab.task
@fab.runs_once
def res_server_start():
    ip2mac = {}
    fab.execute(collect_ip2mac_map, ip2mac)
    fab.execute(res_server_kickoff, ip2mac)

@fab.task
@fab.parallel
def res_server_stop():
    screen_stop_session('res_server')

################################################################################
# start/stop exps and make output dirs

@fab.task
@fab.parallel
def makeout(out_dir='~/data/test', trial_dir=None, unique=True):
    expanduser_cmd = "python -c 'import os; print os.path.expanduser(\"{}\")'"
    out_dir = fab.run(expanduser_cmd.format(out_dir))

    i = 0
    while True:
        subdirs = []
        subdirs.append(out_dir)
        subdirs.append('{:03}'.format(i))
        if trial_dir is not None:
            subdirs.append(trial_dir)
        subdirs.append(fab.env.host)

        host_out_dir = '/'.join(subdirs)

        if not(unique) or not(exists(host_out_dir)):
            break

        i +=1

    fab.run('mkdir -p "{}"'.format(host_out_dir))
    return host_out_dir

@fab.task
@fab.parallel
def setup():
    rm_proxy()
    time_sync()
    install_python_deps()
    network(freq=5180)
    # iperf_start_servers()


@fab.task
@fab.parallel
def stop_exp():
    stop_react()
    stop_react2()
    res_server_stop()

    iperf_stop_clients()
    opus_stop_receivers()
    opus_stop_streamers()

################################################################################
# qosium setup

@fab.task
def stop_scopes():
    screen_stop_scopes()

@fab.task
def stop_probes():
    screen_stop_probes()

def update_ini_file(addr_1, addr_2, out_dir):
    with open('/users/dkulenka/qosium_scope_lite.ini.template', 'r') as f:
        data = f.readlines()

        print data

    data[33-1] = 'qm_probe_addresses {};{}\n'.format(addr_2, addr_1)
    data[36-1] = 'qm_probe_ports 8177;8177\n'
    data[52-1] = 'default_intrf 1\n'
    data[106-1] = 'packet_filter ip and host {} and host {} and (udp.srcport >= 5000) and (udp.srcport < 5010)\n'.format(addr_1, addr_2) # TODO: Check if this worked, I added the udp source port info#  
    data[125-1] = 'packet_filter_mode 1\n'
    data[131-1] = 'get_pk_info_results 1\n'
    data[137-1] = 'get_pk_qos_results 1\n'
    data[143-1] = 'get_pcap_results 1\n'
    data[151-1] = 'pk_info_to_file 1\n'
    data[154-1] = 'average_to_file 1\n'
    data[157-1] = 'pk_qos_to_file 1\n'
    data[160-1] = 'pcap_to_file 1\n'
    data[163-1] = 'flows_to_file 1\n'
    data[170-1] = 'file_target_path {}'.format(out_dir)
    data[195-1] = 'pk_id_method 0'

    with open('/users/dkulenka/qosium_scope_lite.ini', 'w') as f:
        f.writelines(data)

    # copy the updated .ini file to the Qosium folder
    fab.sudo('cp /users/dkulenka/qosium_scope_lite.ini /opt/QosiumProbe/bin/')


@fab.task
def setup_measurement(meas_matrix, out_dir):
    # TODO: Make it so you can have multiple probes setup on each node
    for key in meas_matrix.matches.keys():
        if get_my_ip() == key:
            screen_start_session('probe', 'sudo sh /opt/QosiumProbe/bin/runQosiumProbe.sh')
            
    time.sleep(2)

    for link in meas_matrix.links(get_my_ip()):
        """
        If we get inside this for loop, it means that we need to set the current node
        as the measurement point, and connect to the probe running at the link. So we
        need to update the qosium ini file on this node. 

        TODO: Make a function that starts a probe running on a node in a screen session
        """
        update_ini_file(get_my_ip(dev='eth0'), get_foreign_ip(link), out_dir)

        screen_start_session('scope', 'sudo sh /opt/QosiumProbe/bin/runQosiumScopeLite.sh')

@fab.task
def start_qos_measurement(meas_matrix):  
    """
    This function sends all the setup commands to the qosium scope screen. 
    The scope needs to be running inside a screen session on the node, with 
    the screen session name of 'scope'. 
    """ 
    for link in meas_matrix.links(get_my_ip()):
        screen_run_command('scope', 'connect\r')
        screen_run_command('scope', 'subscribe\r')
        screen_run_command('scope', 'setparams\r')
        screen_run_command('scope', 'setifs\r')
        screen_run_command('scope', '1\r')
        screen_run_command('scope', '1\r')
        screen_run_command('scope', 'startmeas\r')

@fab.task
def stop_qos_measurement(meas_matrix):
    """
    Stops the qosium probe measurement by sending commands to the screen
    session called 'scope', stopping the measurement and disconnecting from
    the probes. 
    """
    for link in meas_matrix.links(get_my_ip()):
        screen_run_command('scope', 'stopmeas')
        screen_run_command('scope', 'disconnect')

@fab.task
def test_exp():
    mm = MeasMatrix() 
    mm.add('192.168.0.1', r'192.168.0.2')
    mm.add('192.168.0.2', r'NONE')

    setup_measurement(mm, '')
    
    start_qos_measurement(mm)

    time.sleep(30)
    stop_qos_measurement(mm)

################################################################################
# topos

def topo(tname, host_out_dir, tcp):
    cm = ConnMatrix()

    if tname == 'star':
        cm.add('192.168.0.1', r'192.168.0.5')
        cm.add('192.168.0.2', r'192.168.0.5')
        cm.add('192.168.0.3', r'192.168.0.5')
        cm.add('192.168.0.4', r'192.168.0.5')
        cm.add('192.168.0.5', r'NONE')
    elif tname == '3hop':
        cm.add('192.168.0.1', r'192.168.0.2')
        cm.add('192.168.0.2', r'192.168.0.3')
        cm.add('192.168.0.3', r'192.168.0.2')
        cm.add('192.168.0.4', r'192.168.0.3')
    elif tname == 'bae':
        cm.add('192.168.0.1', r'192.168.0.2')
        cm.add('192.168.0.2', r'192.168.0.3')
        cm.add('192.168.0.3', r'192.168.0.4')
        cm.add('192.168.0.4', r'192.168.0.1')
    else:
        assert False, 'Topo does not exist right now mate'

    iperf_start_clients(host_out_dir, cm, tcp)



def get_CM():
    cm = ConnMatrix()

    cm.add('192.168.0.1', r'192.168.0.2')
    cm.add('192.168.0.2', r'192.168.0.3')
    cm.add('192.168.0.3', r'192.168.0.4')
    cm.add('192.168.0.4', r'192.168.0.1')
    return cm

def get_MM():
    mm = MeasMatrix()
    mm.add('192.168.0.1', r'192.168.0.2')
    mm.add('192.168.0.2', r'NONE')
    return mm

def new_topo(tname):
    cm = ConnMatrix()
    if tname == 'star':
        cm.add('192.168.0.1', r'NONE')
        cm.add('192.168.0.2', r'192.168.0.5')
        cm.add('192.168.0.3', r'192.168.0.5')
        cm.add('192.168.0.4', r'192.168.0.5')
        cm.add('192.168.0.5', r'NONE')
    elif tname == '3hop':
        cm.add('192.168.0.1', r'192.168.0.2')
        cm.add('192.168.0.2', r'192.168.0.3')
        cm.add('192.168.0.3', r'192.168.0.2')
        cm.add('192.168.0.4', r'192.168.0.3')
    elif tname == 'complete_flow':
        cm.add('192.168.0.1', r'NONE')
        cm.add('192.168.0.2', r'192.168.0.3')
        cm.add('192.168.0.3', r'192.168.0.4')
        cm.add('192.168.0.4', r'192.168.0.1')
    elif tname == 'complete_cross':
        cm.add('192.168.0.1', r'192.168.0.3')
        cm.add('192.168.0.2', r'192.168.0.4')
        cm.add('192.168.0.3', r'192.168.0.1')
        cm.add('192.168.0.4', r'192.168.0.2')
    elif tname == 'single_hop_single_flow':
        cm.add('192.168.0.1', r'192.168.0.2')
        cm.add('192.168.0.2', r'NONE')
    elif tname == 'single_hop_duplex_flow':
        cm.add('192.168.0.1', r'192.168.0.2')
        cm.add('192.168.0.2', r'192.168.0.1')
    elif tname == 'new_single_udp':
        cm.add('192.168.0.1', r'192.168.0.2')
        cm.add('192.168.0.4', r'192.168.0.2')
        cm.add('192.168.0.3', r'192.168.0.2')
        cm.add('192.168.0.5', r'192.168.0.2')
        cm.add('192.168.0.6', r'192.168.0.2')
        cm.add('192.168.0.2', r'NONE')
    elif tname == 'new_single_rtp':
        cm.add('192.168.0.2', r'192.168.0.6')
        cm.add('192.168.0.6', r'NONE')
    elif tname == 'exposed':
        cm.add('192.168.0.2', r'192.168.0.1')
        cm.add('192.168.0.1', r'NONE')
        cm.add('192.168.0.3', r'192.168.0.4')
        cm.add('192.168.0.4', r'NONE')
    else:
        assert False, 'Topo does not exist right now mate'

    return cm

################################################################################
# exps

# For the star topology:
# nodes: B2, F1, F4, I4, F3

# Ford the complete topology:
# nodes: K1, K2, K3, K4

# For the 3-hop line
# nodes: B2, F3, I4, M20


@fab.task
def get_number_of_nodes():
    with open('/users/dkulenka/repo/node_info.txt') as f:
        lines = f.readlines()

    nodes = []
    for line in lines:
        if not line.startswith('#'):
            nodes += line

    return len(nodes)

def update_node_file(num):
    with open('/users/dkulenka/repo/node_info.txt', 'r') as f:
        data = f.readlines()

        print data

    for i in xrange(len(data)):
        if data[i].startswith('#') and i < num:
            data[i] = data[i][1:]
    
    print data
    with open('/users/dkulenka/repo/node_info.txt', 'w') as f:
        f.writelines(data)

@fab.task
@fab.parallel
def ip2mac_test():
    ip2mac = {}
    fab.execute(collect_ip2mac_map, ip2mac)

########################################################################################################
### BELOW HERE ARE MY EXPERIMENTS
########################################################################################################

@fab.task
@fab.runs_once
def butterfly():

    @fab.task
    @fab.parallel
    def single(use):
        host_out_dir = makeout('~/data/butterfly/{}'.format(use))

        if use == 'react':
            run_react(host_out_dir, use)
        else:
            stop_react()
            stop_react2()

        udp_cm = new_topo('new_single_udp')
        rtp_cm = new_topo('new_single_rtp')

        mm = MeasMatrix()
        mm.add('192.168.0.2', r'192.168.0.5')
        mm.add('192.168.0.5', r'NONE')

        setup_measurement(mm, host_out_dir)

        print('Starting iperf servers')
        iperf_start_servers()
        print('Starting opus receivers')
        opus_start_receivers_new(host_out_dir, rtp_cm)
        print('Waiting for servers to start up')
        time.sleep(10)

        print('Starting iperf streams')
        iperf_start_clients(host_out_dir, udp_cm, tcp=False)
        print('Waiting for iperf streams to start')
        time.sleep(5)
        print('Starting opus streamers')
        opus_start_streamers_new(host_out_dir, rtp_cm)

        print('Giving stream a while to start')
        time.sleep(10)

        print('Starting Qosium')
        start_qos_measurement(mm)

        print('Waiting -- Running experiment')
        time.sleep(120)

        stop_qos_measurement(mm)

    times_to_run = 5
    for use in ['802', 'react']:
        for i in xrange(times_to_run):
            fab.execute(single, use)
            fab.execute(screen_stop_all)
            time.sleep(20)

@fab.task
@fab.runs_once
def hidden():

    @fab.task
    @fab.parallel
    def single(use):
        host_out_dir = makeout('~/data/hidden/{}'.format(use))

        if use == 'react':
            run_react(host_out_dir, use)
        else:
            stop_react()
            stop_react2()

        udp_cm = ConnMatrix()
        cm.add('192.168.0.1', r'192.168.0.2')
        cm.add('192.168.0.2', r'NONE')
        cm.add('192.168.0.3', r'192.168.0.2')

        rtp_cm = ConnMatrix()
        cm.add('192.168.0.1', r'192.168.0.2')
        cm.add('192.168.0.2', r'NONE')

        mm = MeasMatrix()
        mm.add('192.168.0.1', r'192.168.0.2')
        mm.add('192.168.0.2', r'NONE')

        setup_measurement(mm, host_out_dir)

        print('Starting iperf servers')
        iperf_start_servers()
        print('Starting opus receivers')
        opus_start_receivers_new(host_out_dir, rtp_cm)
        print('Waiting for servers to start up')
        time.sleep(10)

        print('Starting iperf streams')
        iperf_start_clients(host_out_dir, udp_cm, tcp=False)
        print('Waiting for iperf streams to start')
        time.sleep(5)
        print('Starting opus streamers')
        opus_start_streamers_new(host_out_dir, rtp_cm)

        print('Giving stream a while to start')
        time.sleep(10)

        print('Starting Qosium')
        start_qos_measurement(mm)

        print('Waiting -- Running experiment')
        time.sleep(120)

        stop_qos_measurement(mm)

    times_to_run = 5
    for use in ['802', 'react']:
        for i in xrange(times_to_run):
            fab.execute(single, use)
            fab.execute(screen_stop_all)
            time.sleep(20)


@fab.task
@fab.runs_once
def hidden_term():

    @fab.task
    @fab.parallel
    def single(use):
        host_out_dir = makeout('~/data/hidden_term/{}'.format(use))

        if use == 'new':
            run_react(host_out_dir, use)
        else:
            stop_react()
            stop_react2()

        udp_cm = new_topo('complete_flow')
        rtp_cm = ConnMatrix()
        rtp_cm.add('192.168.0.1', r'192.168.0.3')
        rtp_cm.add('192.168.0.3', r'NONE')

        mm = MeasMatrix()
        mm.add('192.168.0.1', r'192.168.0.3')
        mm.add('192.168.0.3', r'NONE')

        setup_measurement(mm, host_out_dir)

        print('Starting iperf servers')
        iperf_start_servers()
        print('Starting opus receivers')
        opus_start_receivers_new(host_out_dir, rtp_cm)
        print('Waiting for servers to start up')
        time.sleep(10)

        print('Starting iperf streams')
        iperf_start_clients(host_out_dir, udp_cm, tcp=False)
        print('Waiting for iperf streams to start')
        time.sleep(5)
        print('Starting opus streamers')
        opus_start_streamers_new(host_out_dir, rtp_cm)

        print('Giving stream a while to start')
        time.sleep(10)

        print('Starting Qosium')
        start_qos_measurement(mm)

        print('Waiting -- Running experiment')
        time.sleep(120)

        stop_qos_measurement(mm)

    times_to_run = 5
    for use in ['dot', 'new']:
        for i in xrange(times_to_run):
            fab.execute(single, use)
            fab.execute(screen_stop_all)
            time.sleep(20)


@fab.task
@fab.runs_once
def star():

    @fab.task
    @fab.parallel
    def start_exp(use):
        host_out_dir = makeout('~/data/star/{}'.format(use))

        if use == 'new':
            run_react(host_out_dir, use)
        else:
            stop_react()
            stop_react2()

        udp_cm = new_topo('star')
        rtp_cm = ConnMatrix()
        rtp_cm.add('192.168.0.1', r'192.168.0.5')
        # rtp_cm.add('192.168.0.2', r'NONE')
        # rtp_cm.add('192.168.0.3', r'NONE')
        # rtp_cm.add('192.168.0.4', r'NONE')
        rtp_cm.add('192.168.0.5', r'NONE')

        mm = MeasMatrix()
        mm.add('192.168.0.1', r'192.168.0.5')
        mm.add('192.168.0.5', r'NONE')

        setup_measurement(mm, host_out_dir)

        print('Starting iperf servers')
        iperf_start_servers()
        print('Starting opus receivers')
        opus_start_receivers_new(host_out_dir, rtp_cm)
        print('Waiting for servers to start up')
        time.sleep(10)

        print('Starting iperf streams')
        iperf_start_clients(host_out_dir, udp_cm, tcp=False)
        print('Waiting for iperf streams to start')
        time.sleep(5)
        print('Starting opus streamers')
        opus_start_streamers_new(host_out_dir, rtp_cm)

        print('Giving stream a while to start')
        time.sleep(10)

        print('Starting Qosium')
        start_qos_measurement(mm)

        print('Waiting -- Running experiment')
        time.sleep(120)

        stop_qos_measurement(mm)

    times_to_run = 5
    for use in ['dot', 'new']:
        for i in xrange(times_to_run):
            fab.execute(start_exp, use)
            fab.execute(screen_stop_all)
            time.sleep(20)


@fab.task
@fab.runs_once
def exposed():

    @fab.task
    @fab.parallel
    def start_exp(use):
        host_out_dir = makeout('~/data/exposed/{}'.format(use))

        if use == 'new':
            run_react(host_out_dir, use)
        else:
            stop_react()
            stop_react2()

        udp_cm = new_topo('exposed')
        rtp_cm = ConnMatrix()
        rtp_cm.add('192.168.0.1', r'192.168.0.2')
        # rtp_cm.add('192.168.0.2', r'NONE')
        # rtp_cm.add('192.168.0.3', r'NONE')
        # rtp_cm.add('192.168.0.4', r'NONE')
        rtp_cm.add('192.168.0.2', r'NONE')

        mm = MeasMatrix()
        mm.add('192.168.0.1', r'192.168.0.2')
        mm.add('192.168.0.2', r'NONE')

        setup_measurement(mm, host_out_dir)

        print('Starting iperf servers')
        iperf_start_servers()
        print('Starting opus receivers')
        opus_start_receivers_new(host_out_dir, rtp_cm)
        print('Waiting for servers to start up')
        time.sleep(10)

        print('Starting iperf streams')
        iperf_start_clients(host_out_dir, udp_cm, tcp=False)
        print('Waiting for iperf streams to start')
        time.sleep(5)
        print('Starting opus streamers')
        opus_start_streamers_new(host_out_dir, rtp_cm)

        print('Giving stream a while to start')
        time.sleep(10)

        print('Starting Qosium')
        start_qos_measurement(mm)

        print('Waiting -- Running experiment')
        time.sleep(120)

        stop_qos_measurement(mm)

    times_to_run = 5
    for i in xrange(times_to_run):
        for use in ['dot', 'new']:
                fab.execute(start_exp, use)
                fab.execute(screen_stop_all)
                time.sleep(20)




@fab.task
@fab.runs_once
def line():
    ip2mac = {}
    fab.execute(collect_ip2mac_map, ip2mac)

    last = None
    for ip in ip2mac:
        if last is None or ip > last:
            last = ip
    last = long2dot(last)

    def multi_makeout(use, stream):
        # makeout(out_dir, trial_dir, unique (T or F))
        return makeout('~/data/line_new/', '{}-{}-{}'.format(len(ip2mac), use, stream))

    @fab.task
    @fab.parallel
    def multi(use, stream):
        host_out_dir = multi_makeout(use, stream) 
        print('OUT DIR: {}'.format(host_out_dir)) 
        if use == 'new':
            status = json.loads(fab.run(
                    '{}/reservation/reserver.py get_status {}'.format(
                    project_path, get_my_ip())))
            capacity = float(status['capacity'])/100.0
            allocation = float(status['allocation'])/100.0
            # if get_my_ip() == '192.168.0.1':
            #     allocation = 5.0/100.0
            # elif get_my_ip() == '192.168.0.2':
            #     allocation = 35.0/100.0
            # elif get_my_ip() == '192.168.0.3':
            #     allocation = 35.0/100.0
            # else:
            #     allocation = 5.0/100.0

            run_react(host_out_dir, use, capacity=capacity, prealloc=allocation)
        else:
            stop_react()
            stop_react2()

        cm = ConnMatrix()
        cm.add('192.168.0.1', last)
        cm.add(last, r'NONE')

        # congestion_cm = ConnMatrix()
        # congestion_cm.add('192.168.0.1', last)
        # congestion_cm.add(last, r'NONE')

        mm = MeasMatrix()
        mm.add('192.168.0.1', last)
        mm.add(last, r'NONE')

        setup_measurement(mm, host_out_dir)


        if stream == 'opus':
            print('Starting iperf servers')
            iperf_start_servers()
            print('Starting opus receivers')
            opus_start_receivers_new(host_out_dir, cm)
            print('Waiting for receivers to start up')
            time.sleep(10)

            # Below is the congestion streams, commented out to see RTP performance
            # print('Starting iperf streams')
            # iperf_start_clients(host_out_dir, congestion_cm, tcp=False)
            # print('Waiting for iperf streams to start')
            # time.sleep(5)
            print('Starting opus streamers')
            opus_start_streamers_new(host_out_dir, cm)

        elif stream == 'iperf':
            print('Starting iperf servers')
            iperf_start_servers()
            print('Waiting for server startup')
            time.sleep(10)

            print('Starting iperf clients -- 1G')
            iperf_start_clients(host_out_dir, cm, tcp=False)
        elif stream == 'iperf_low':
            print('Starting iperf servers')
            iperf_start_servers()
            print('Waiting for server startup')
            time.sleep(10)

            print('Starting iperf clients -- 1M')
            iperf_start_clients(host_out_dir, cm, tcp=False, rate='1M')

        print('Giving streams a while to start')
        time.sleep(10)

        print('Starting Qosium')
        start_qos_measurement(mm)

        print('Waiting -- running experiment')
        time.sleep(120)

        stop_qos_measurement(mm)
        # print('Stopping experiment. Check output directory for data info. ')
        # fab.execute(stop_exp)

    times_to_run = 5
    for use in ['dot', 'new']:
        for stream in ['opus']:
            for i in xrange(times_to_run):
                if use == 'react':
                    fab.execute(res_server_kickoff, ip2mac)
                    time.sleep(5)

                    allocation = int(math.floor(80 / get_number_of_nodes()))

                    # # reserve for RTP stream
                    # allocation = 5
                    resp = fab.run(
                            '{}/reservation/reserver.py place_reservation' \
                            ' 192.168.0.1 {} {}'.format(project_path, last, allocation))
                    assert json.loads(resp)['placed']

                    # # reserve for UDP stream
                    # allocation = 65
                    # resp = fab.run(
                    #         '{}/reservation/reserver.py place_reservation' \
                    #         ' 192.168.0.2 192.168.0.3 {}'.format(project_path, allocation))
                    # assert json.loads(resp)['placed']


                print('Running experiment: MAC = {}'.format(use))
                fab.execute(multi, use, stream)
                fab.execute(screen_stop_all)
                time.sleep(20)
                

########################################################################################################
### BELOW HERE IS MATT'S OLD CODE
########################################################################################################

@fab.task
@fab.runs_once
def exp_betak(tname):
    assert tname == 'star' or tname == '3hop' or tname == 'bae'

    @fab.task
    @fab.parallel
    def betak(out_dir, tname, beta, k):
        host_out_dir = makeout(out_dir, '{:03}-{:04}'.format(int(beta*100), k))
        run_react(host_out_dir, 'new', beta, k)
        topo(tname, host_out_dir, False)

    betas = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]

    for beta in betas:
        for k in range(250, 3250, 250):
            fab.execute(betak, '~/data/97_betak/{}'.format(tname), tname,
                    beta, k)
            time.sleep(15)
            fab.execute(stop_exp)

@fab.task
@fab.runs_once
def exp_comp(tname):

    @fab.task
    @fab.parallel
    def comp(out_dir, tname, use):
        host_out_dir = makeout(out_dir, use)
        if use != 'oldest':
            run_react(host_out_dir, use)
        else:
            run_react2(host_out_dir)
        topo(tname, host_out_dir, False)

    for use in  ['dot', 'new', 'old', 'oldest']:
        fab.execute(comp, "~/data/96_comp/{}".format(tname), tname, use)
        time.sleep(120)
        fab.execute(stop_exp)

@fab.task
@fab.runs_once
def exp_multi():
    ip2mac = {}
    fab.execute(collect_ip2mac_map, ip2mac)

    last = None
    for ip in ip2mac:
        if last is None or ip > last:
            last = ip
    last = long2dot(last)

    def multi_makeout(use, tcp):
        return makeout('~/data/95_multi/', '{}-{}-{}'.format(len(ip2mac), use,
                'tcp' if tcp else 'udp'))

    @fab.task
    @fab.parallel
    def multi(use, tcp):
        host_out_dir = multi_makeout(use, tcp)

        if use == 'react':
            status = json.loads(fab.run(
                    '{}/reservation/reserver.py get_status {}'.format(
                    project_path, get_my_ip())))
            capacity = float(status['capacity'])/100.0
            allocation = float(status['allocation'])/100.0
            run_react(host_out_dir, use, capacity=capacity, prealloc=allocation)
        else:
            stop_react()
            stop_react2()

        cm = ConnMatrix()
        cm.add('192.168.0.1', last)
        cm.add(last, r'NONE')
        #roadtrip_start_clients(host_out_dir, cm, tcp)
        iperf_start_clients(host_out_dir, cm, tcp)

    for use in ['802', 'react']:
        for tcp in [True, False]:
            for i in xrange(1):
                if use == 'new':
                    fab.execute(res_server_kickoff, ip2mac)
                    time.sleep(1) # wait for server to start

                    resp = fab.run(
                            '{}/reservation/reserver.py place_reservation' \
                            ' 192.168.0.1 {} 26'.format(project_path, last))
                    assert json.loads(resp)['placed']

                print("Running experiment: MAC = {}; tcp = {}".format(use, tcp))
                fab.execute(multi, use, tcp)
                time.sleep(120)
                fab.execute(stop_exp)
                
                
@fab.task
@fab.parallel
def exp_4con(use):
    assert(use == "dot" or use == "new" or use == "old" or use == 'oldest')

    host_out_dir = makeout('~/data/01_4con', use)

    cm = ConnMatrix()
    cm.add('192.168.0.1', r'192.168.0.2')
    cm.add('192.168.0.2', r'192.168.0.3')
    cm.add('192.168.0.3', r'192.168.0.4')
    cm.add('192.168.0.4', r'192.168.0.1')
    iperf_start_clients(host_out_dir, cm, tcp=True)

    if use != 'oldest':
        run_react(host_out_dir, use)
    else:
        run_react2(host_out_dir)

@fab.task
@fab.parallel
def exp_line(use):
    assert(use == "dot" or use == "new" or use == "old")

    host_out_dir = makeout('~/data/10_line', use)

    cm = ConnMatrix()
    cm.add('192.168.0.1', r'192.168.0.4')
    iperf_start_clients(host_out_dir, cm)

    run_react(host_out_dir, use)

@fab.task
@fab.parallel
def exp_longline(dot, udp=True, flows=1):
    #NAME = '{}lowflow'.format(flows)
    NAME = 'manyflow'.format(flows)

    cm = ConnMatrix()
    cm.add('192.168.0.1', r'192.168.0.2$')
    cm.add('192.168.0.2', r'192.168.0.1$')
    cm.add('192.168.0.3', r'192.168.0.4$')
    cm.add('192.168.0.4', r'192.168.0.3$')
    cm.add('192.168.0.5', r'192.168.0.6$')
    cm.add('192.168.0.6', r'192.168.0.5$')
    cm.add('192.168.0.7', r'192.168.0.8$')
    cm.add('192.168.0.8', r'192.168.0.7$')
    cm.add('192.168.0.9', r'192.168.0.10$')
    cm.add('192.168.0.10', r'192.168.0.9$')

    trial = '{}_{}_{}'.format(NAME, 'udp' if udp else 'tcp',
            'dot' if dot else 'new')
    host_out_dir = makeout('~/data/11_longline', trial)

    iperf_start_clients(host_out_dir, cm, tcp=not(udp))
    #iperf_start_clients(host_out_dir, cm, rate='1M')
    run_react(host_out_dir, 'dot' if dot else 'new')

@fab.task
@fab.runs_once
def runner():
    for dot in [True, False]:
        for udp in [True, False]:
        #for flows in [1, 2]:
            fab.execute(exp_longline, dot, udp=udp)
            time.sleep(240)
            fab.execute(stop_exp)

@fab.task
@fab.parallel
def exp_concept(enable_react):
    enable_react = bool(strtobool(enable_react))

    subdir = 'react_on' if enable_react else 'react_off'
    host_out_dir = makeout('~/data/01_concept', subdir)

    cm = ConnMatrix()
    cm.add('192.168.0.1', r'192.168.0.2')
    cm.add('192.168.0.2', r'192.168.0.3')
    cm.add('192.168.0.3', r'192.168.0.4')
    cm.add('192.168.0.4', r'192.168.0.1')
    iperf_start_clients(host_out_dir, cm)

    run_react(host_out_dir, 'new' if enable_react else None)

@fab.task
@fab.parallel
def exp_graph2():
    host_out_dir = makeout('~/data/98_graph2')

    nodes = range(len(fab.env.hosts))
    random.shuffle(nodes)

    cmd = 'ping -c 100 -I wlan0 192.168.0.{0} > {1}/192.168.0.{0}'
    for n in nodes:
        with fab.settings(warn_only=True):
            fab.run(cmd.format(n + 1, host_out_dir))

@fab.task
@fab.parallel
def exp_test(enable_react=False, tcp=True):
    if isinstance(enable_react, basestring):
        enable_react = bool(strtobool(enable_react))
    if isinstance(tcp, basestring):
        tcp = bool(strtobool(tcp))

    host_out_dir = makeout()

    cm = ConnMatrix()
    cm.add('192.168.0.1', r'192.168.0.2')
    cm.add('192.168.0.2', r'192.168.0.3')
    cm.add('192.168.0.3', r'192.168.0.4')
    cm.add('192.168.0.4', r'192.168.0.1')
    iperf_start_clients(host_out_dir, cm)

    if enable_react:
        run_react(host_out_dir, tcp=tcp)




#########################################################################################
#### 534 Project Functions ##############################################################
#########################################################################################

factors = [
    'threshold', 
    'transport', 
    'bandwidth', 
    'num_flow1', 
    'num_flow2', 
    'num_flow3',
    'num_flow4',
    'prealloc',
    'beta',
    'k'
]

levels = [
    [50, 75, 80, 90],
    ['tcp', 'udp'],
    ['500K', '1M', '10M', '50M', '100M', '1G'],
    [1, 2, 3, 4],
    [1, 2, 3, 4],
    [1, 2, 3, 4],
    [1, 2, 3, 4],
    ['yes', 'no'],
    [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
    [250, 500, 750, 1000, 1250, 1500, 1750, 2000, 2250, 2500, 2750, 3000]
]

def get_LA_rows():
    with open('la.tsv', 'r') as f:
        lines = f.readlines()
    num_rows = int(lines[1].split('\t')[0].strip())
    num_params = int(lines[1].split('\t')[1].strip())

    params = []

    for param in lines[2].split('\t'):
        params.append(param.strip())
    params = params[:-1]
    params = [int(param) for param in params]

    first_row = 3+num_params+1


    rows = []
    i = 0
    for row in range(first_row, num_rows+first_row):
        run = [line.strip() for line in lines[row].split('\t')][:-1]
        run = [int(r) for r in run]
        run.insert(0,i)
        i += 1
        rows.append(run)

    random.shuffle(rows)
    return rows

@fab.task
def iperf_start_clients_new(host_out_dir, conn_matrix, tcp=False, rate='1G', num_flows=1):
    for server in conn_matrix.links(get_my_ip()):
        cmd = 'iperf -c {}'.format(server)
        if not(tcp):
            cmd += ' -u '

        cmd += ' -b {}'.format(rate)
        cmd += ' -P {}'.format(num_flows)
        cmd += ' -t -1 -i 1 -yC'

        # Use -i (ignore signals) so that SIGINT propagted up pipe to iperf
        cmd += ' | tee -i {}/{}.csv'.format(host_out_dir, server)

        screen_start_session('iperf_client', cmd)

@fab.task
def iperf_stop_clients_new():
    screen_stop_session('iperf_client', interrupt=True)

# iperf3 -c 192.168.0.1 -b 1G -i 1 -t -1 -P 1

@fab.task
def try_it():
    host = ''
    cm = ConnMatrix()

    cm.add('192.168.0.1', r'192.168.0.2')
    cm.add('192.168.0.2', r'192.168.0.3')
    cm.add('192.168.0.3', r'192.168.0.4')
    cm.add('192.168.0.4', r'192.168.0.1')

    iperf_start_clients_new(host, cm)

@fab.task
@fab.runs_once
def run_experiments():

    @fab.task
    @fab.parallel
    def screening(run, params):
        host_out_dir = makeout('~/data/screening/run{}/'.format(run))

        threshold = params[0] # done
        transport = params[1] # done
        bandwith = params[2] # done
        if get_my_ip() == '192.168.0.1':
            num_flows = params[3]
        elif get_my_ip() == '192.168.0.2':
            num_flows = params[4]            
        elif get_my_ip() == '192.168.0.3':
            num_flows = params[5]
        elif get_my_ip() == '192.168.0.4':
            num_flows = params[6]
        if params[7] == 'yes':
            prealloc = params[0]
        else:
            prealloc = 0
        # arrangemnet = params[8]
        beta = params[8] # done
        k = params[9] # done

        
        run_react(host_out_dir, tuner='new', beta=beta, k=k, capacity=threshold, prealloc=prealloc)

        # setup connection matrix
        cm = get_CM()

        # cm = ConnMatrix()
        # cm.add('192.168.0.1', r'192.168.0.2')
        # cm.add('192.168.0.2', r'192.168.0.3')
        # cm.add('192.168.0.3', r'192.168.0.4')
        # cm.add('192.168.0.4', r'192.168.0.1') 

        # setup measurement matrix
        mm = get_MM()

        setup_measurement(mm, host_out_dir)

        iperf_start_servers()
        time.sleep(10)

        # start iperf clients

        if transport == 'tcp':
            tcp = True
        else:
            tcp = False

        iperf_start_clients_new(host_out_dir, cm, tcp=tcp, rate=bandwith, num_flows=num_flows)

        # start qos measurement

        print('Giving stream a while to start')
        time.sleep(10)

        print('Starting Qosium')
        start_qos_measurement(mm)

        print('Waiting -- Running experiment')
        time.sleep(5)

        stop_qos_measurement(mm)


        

    runs = get_LA_rows()

    for i in range(len(runs)):
        run_num = runs[i][0]
        print(run_num)
        params = []
        for j in range(1,len(runs[i])):
            params.append(levels[j-1][runs[i][j]])
        
        print("Run: {}".format(run_num))
        print(params)

        fab.execute(screening, run_num, params)
        fab.execute(screen_stop_all)
        time.sleep(20)


