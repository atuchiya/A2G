
import pprint
import math
import numpy as np
from collections import defaultdict

# ネットリスト
def parse_netlist_synthesis(netlist_path = None):

    # 読込
    with open(netlist_path, 'r') as file:
        netlist = file.readlines()

    for line in netlist:
        
        if line.startswith(('x')):
            words = line.split()
            nodes,name = words[1:-1],words[-1]
            print(name,nodes)


if __name__ == '__main__':

    netlist_path = '../file/rx_core.spice'

    parse_netlist_synthesis(netlist_path=netlist_path)
            