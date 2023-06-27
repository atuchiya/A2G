import re
from collections import defaultdict
import sys
import Circuit,pprint

# ネットリスト
def parse_netlist(file_path):
    with open(file_path, 'r') as file:
        netlist = file.readlines()

    # 素子情報
    resistors = []
    capacitors = []
    inductors = []
    sources = []
    devices = []
    params = dict()
    for idx,line in enumerate(netlist):
        if len(line.split()) > 0 and '.param' == line.split()[0]:
            _,name,value,_ = re.split(' |=|\n',line)
            params[name] = value

    for idx,line in enumerate(netlist):
        if line.startswith('R'):
            resistors.append(line.strip())
        elif line.startswith('C'):
            capacitors.append(line.strip())
        elif line.startswith('L'):
            inductors.append(line.strip())
        elif line.startswith(('V', 'I')):
            sources.append(line.strip())
        elif line.startswith('X'):
            words = line.strip()
            for pls_idx in range(1,10):
                if netlist[idx + pls_idx].startswith('+'):
                    words += netlist[idx + pls_idx].strip()
                else:
                    break
            update_words = list()
            for idx,word in enumerate(words.split()):
                for name,value in params.items():
                    if name == word.split('=')[-1]:
                        word = word.replace(name,params[name])
                if idx == 0 or 'sky' in word or word.split('=')[0] in ['W','L','m','MF']:
                    update_words.append(word)
            devices.append(update_words)

    # 配線情報　＆　対称性
    connections = defaultdict(list)
    connections2 = defaultdict(list)
    points_mos = ['D','G','S','B']
    points_res = ['1','2']
    for line in netlist:
        if line.startswith(('R', 'C', 'L', 'V', 'I','X')):
            element_name, *base_nodes, _ = line.strip().split()
            nodes,tar_idx = subarray_until_target_char(base_nodes, 'sky')
            process_name = base_nodes[tar_idx]
            for idx,node in enumerate(nodes):
                if len(nodes) == 4:
                    connections[node].append(element_name + '_' + points_mos[idx])
                    connections2[node].append(process_name + '_' + points_mos[idx])
                elif len(nodes) == 2:
                    connections[node].append(element_name + '_' + str(idx+1))
                    connections2[node].append(process_name + '_' + str(idx+1))
            
    # return {
    #     'resistors': resistors,
    #     'capacitors': capacitors,
    #     'inductors': inductors,
    #     'sources': sources,
    #     'devices':devices
    # }

    return dict(connections)
    # return elements

# 特定の文字を含む要素までの配列
def subarray_until_target_char(array, target_char):
    result = []
    for idx,item in enumerate(array):
        if target_char in item:
            break
        result.append(item)
    return result,idx

# 表示　ー＞　素子
def display_elements(elements):
    for element_type, items in elements.items():
        print(f'{element_type.capitalize()}:')
        for item in items:
            print(f' {item}\n')

# 表示　ー＞　配線
def display_connections(connections):
    for node, connected_elements in connections.items():
        connected_elements = sorted(connected_elements,key = lambda x:x.split('_')[-1])
        print(f'Node {node}:')
        print(f'  Connected elements: {", ".join(connected_elements)}')

# 対称性を見つける
def find_symmetric_elements(elements):
    symmetric_elements = []
    i = 0
    for node1, element1 in elements.items():
        i += 1
        j = 0
        for node2, element2 in elements.items():
            j += 1
            if j > i:
                if sorted(element1) == sorted(element2):
                # if element1.nodes == element2.nodes:
                    symmetric_elements.append((node1, node2))
    return symmetric_elements

# 表示　ー＞　対称性
def display_symmetric_elements(symmetric_elements):
    print("Symmetric elements:")
    for element1, element2 in symmetric_elements:
        print(f"  {element1} - {element2}")

if __name__ == '__main__':
    file_path = 'file/hyscomp.spice'  # ネットリストファイルのパス
    # file_path = 'file/comparator.spice'  # ネットリストファイルのパス

    # 素子
    # elements = parse_netlist(file_path)
    # display_elements(elements)

    # 配線
    connections = parse_netlist(file_path)
    display_connections(connections)

    # elements = parse_netlist(file_path)
    # symmetric_elements = find_symmetric_elements(elements)
    # display_symmetric_elements(symmetric_elements)
