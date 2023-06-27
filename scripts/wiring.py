
from scripts.util import *
from scripts.setting import *
from scripts.nl_solver import *
import scripts.global_value as g

import pprint
import math
import numpy as np
from collections import defaultdict


# ネットリスト
def parse_netlist_wire(netlist_path = None):

    g.CIRCUIT_INFO = dict()

    # サブサーキット
    CIRCUIT_NAME = None
    # ピン名
    PIN_NAMES = None

    # 読込
    with open(netlist_path, 'r') as file:
        netlist = file.readlines()

    # 配線情報　＆　対称性
    connections = defaultdict(list)
    points_mos = ['D','G','S','B']
    points_res = ['1','2','B']
    for line in netlist:
        
        if line.startswith(('R', 'C', 'L', 'V', 'I', 'X')):
            element_name, *base_nodes, _ = line.strip().split()
            nodes,tar_idx = subarray_until_target_char(base_nodes, 'sky')
            process_name = base_nodes[tar_idx]
            for idx,node in enumerate(nodes):
                if len(nodes) == 4:
                    connections[node].append(element_name + '_' + points_mos[idx])
                elif len(nodes) == 3:
                    connections[node].append(element_name + '_' + points_res[idx])
                elif len(nodes) == 2:
                    connections[node].append(element_name + '_' + str(idx+1))
        elif '.subckt' == line.split()[0]:
            CIRCUIT_NAME,PIN_NAMES = line.split()[1],line.split()[2:]

    g.CIRCUIT_INFO['name'] = CIRCUIT_NAME
    g.CIRCUIT_INFO['pin'] = PIN_NAMES
    g.CIRCUIT_INFO['connect'] = connections

# 特定の文字を含む要素までの配列
def subarray_until_target_char(array, target_char):
    result = []
    for idx,item in enumerate(array):
        if target_char in item:
            break
        result.append(item)
    return result,idx

# 配線箇所を決める
def wiring_points():

    print(f'\nDEBUG\n')

    middle_point = ((np.array(g.CIRCUIT_INFO['size'])-1)/2).tolist()
    tanshi_coords = dict()
    for name,contents in g.DEVICE_INFO.items():
        """
        改善余地アリ -> 候補座標を増やす
        """
        print(f'dname = {name}')
        
        center_points = contents['center_points']
        connections1 = contents['connections']
        connections2 = contents['connections2']

        for what,base_points in connections1.items():
            
            # 順転
            points = np.array(center_points) + np.array(base_points)
            k_point = tuple(points[len(points)//2])

            tanshi_coords[name + '_' + what] = {k_point:points}
            print(what,base_points)

            # 反転
            points = np.array(center_points) + np.array(base_points)*-1
            k_point = tuple(points[len(points)//2])

            tanshi_coords[name + '_' + what][k_point] = points

    final_coords = dict()
    wire_pare = list()

    temp_save = dict()
    sequence_connect = list(g.CIRCUIT_INFO['connect'].keys())
    sequence_connect.remove('vdd')
    sequence_connect.remove('vss')
    sequence_connect = sorted(sequence_connect,key=lambda x:len(x)) + ['vdd','vss','clk']

    

    for node in sequence_connect:
        if node not in g.CIRCUIT_INFO['connect'].keys():
            continue
        tanshi_names = g.CIRCUIT_INFO['connect'][node]
        
        tanshi_names = [tanshi_name for tanshi_name in tanshi_names if 'B' not in tanshi_name]

        print(node,tanshi_names)

        # if node == 'clk':
        #     continue

        if node in ['vdd','vss']:
            """
            ラベル付ける
            """
            # print(node,tanshi_names)
            for tanshi_name in tanshi_names:
                coords = list(tanshi_coords[tanshi_name].keys())
                coords = list(set(coords)-set(temp_save.values()))
                if tanshi_name in temp_save.keys():
                    coords = [temp_save[tanshi_name]]
                coord = coords[0]
                save_coord = tuple([int(coord[0]),int(coord[1]),0])
                final_coords[tanshi_name] = save_coord
                final_coords[node+'-'+tanshi_name] = save_coord

                temp_save[tanshi_name] = coord
        
        elif len(tanshi_names) == 1:
            """
            ラベル付ける
            """
            for tanshi_name in tanshi_names:
                coords = list(tanshi_coords[tanshi_name].keys())
                max_dist = 0
                max_coord = None
                for coord in coords:
                    if coord[1]<middle_point[1]:
                        dist = middle_point[1] - coord[1]
                    else:
                        dist = coord[1] - middle_point[1]
                    if dist > max_dist:
                        max_dist = dist
                        max_coord = coord
                save_coord = tuple([int(max_coord[0]),int(max_coord[1]),0])
                final_coords[tanshi_name] = save_coord
                final_coords[node+'-'+tanshi_name] = save_coord

                temp_save[tanshi_name] = max_coord
                
        else:
            coords = [list(tanshi_coords[tanshi_name].keys()) for tanshi_name in tanshi_names]

            # print(coords)
            # print(tanshi_names)
            # print(coords)
            # print()
            
            connect_pares = list()
            points_pares = list()

            min_data = list()
            idx1 = 0
            for tanshi,coord_candidate in zip(tanshi_names,coords):
                idx1 += 1
                idx2 = 0
                for tanshi2,coord2_candidate in zip(tanshi_names,coords):
                    idx2 += 1
                    if idx2 <= idx1:
                        continue

                    # print()
                    # print(coord_candidate,coord2_candidate)
                    # pprint.pprint(temp_save)
                    coord_candidate = list(set(coord_candidate)-set(temp_save.values()))
                    coord2_candidate = list(set(coord2_candidate)-set(temp_save.values()))
                    if tanshi in temp_save.keys():
                        coord_candidate = [temp_save[tanshi]]
                    if tanshi2 in temp_save.keys():
                        coord2_candidate = [temp_save[tanshi2]]

                    min_tanshi_pare = (tanshi,tanshi2)
                    # print(tanshi,tanshi2)
                    # print(coord_candidate,coord2_candidate)
                    min_coord_pair,min_distance,_ = find_min_distance_pair(coord_candidate, coord2_candidate)

                    min_data.append([min_tanshi_pare,min_coord_pair,min_distance])

            min_data = sorted(min_data,key = lambda x:x[-1])
            pprint.pprint(min_data)

            if len(min_data) == 1:
                connect_pares.append(min_data[0][0])
                points_pares.append(min_data[0][1])
                temp_save[min_data[0][0][0]] = min_data[0][1][0]
                temp_save[min_data[0][0][1]] = min_data[0][1][1]

            elif (min_data[0][-1] == min_data[1][-1]):
                connect_pares.append(min_data[0][0])
                connect_pares.append(min_data[1][0])
                points_pares.append(min_data[0][1])
                points_pares.append(min_data[1][1])

                temp_save[min_data[0][0][0]] = min_data[0][1][0]
                temp_save[min_data[0][0][1]] = min_data[0][1][1]
                temp_save[min_data[1][0][0]] = min_data[1][1][0]
                temp_save[min_data[1][0][1]] = min_data[1][1][1]

            elif  (min_data[-2][-1] == min_data[-1][-1]):
                connect_pares.append(min_data[-1][0])
                connect_pares.append(min_data[-2][0])
                points_pares.append(min_data[-1][1])
                points_pares.append(min_data[-2][1])

                temp_save[min_data[-1][0][0]] = min_data[-1][1][0]
                temp_save[min_data[-1][0][1]] = min_data[-1][1][1]
                temp_save[min_data[-2][0][0]] = min_data[-2][1][0]
                temp_save[min_data[-2][0][1]] = min_data[-2][1][1]

            else:
                d_set = set()
                for val in min_data:
                    
                    # print(f'd_set -> {d_set}')
                    if set(val[0]) in d_set:
                        continue

                    d_set.add(val[0][0])
                    d_set.add(val[0][1])
                    connect_pares.append(val[0])
                    points_pares.append(val[1])
                    temp_save[val[0][0]] = val[1][0]
                    temp_save[val[0][1]] = val[1][1]
                    if len(d_set) == len(tanshi_names):
                        break

            for cp,pp in zip(connect_pares,points_pares):
                wire_pare.append([cp,pp])

    # pprint.pprint(wire_pare)
    # sys.exit()


    # solverの準備
    sg_list = dict()
    key_dict = dict()
    temp_save = dict()
    cnt = 0
    
    
    """
    配線する座標対を決める
    """
    for tanshis,points in wire_pare:
        tanshi1,tanshi2 = tanshis
        can1 = tanshi_coords[tanshi1][points[0]]
        can2 = tanshi_coords[tanshi2][points[1]]
        min_dist,min_pare = 10000,None
        
        for idx1,p1 in enumerate(can1):
            for idx2,p2 in enumerate(can2):
                dist = math.dist(p1,p2)
                if dist < min_dist:
                    min_dist = dist
                    min_pare = [(p1,p2)]
                elif dist == min_dist:
                    min_pare.append((p1,p2))

        cnt += 1
        s_pos,g_pos = min_pare[len(min_pare)//2]
        sx,sy = int(s_pos[0]),int(s_pos[1])
        gx,gy = int(g_pos[0]),int(g_pos[1])
        sg_list[str(cnt)] = [[sx,sy,0],[gx,gy,0]]

        key_dict[str(cnt)] = tanshis
        temp_save[(tanshi1,tanshi2)] = tuple(sg_list[str(cnt)][0])
        temp_save[(tanshi2,tanshi1)] = tuple(sg_list[str(cnt)][1])

    pprint.pprint(temp_save)
    

    """
    対称座標対を見つける
    """

    pprint.pprint(sg_list)

    search = dict()
    for key,val in sg_list.items():
        search[tuple(val[0][:2])] = key
        search[tuple(val[1][:2])] = key
    for y_idx in range(g.CIRCUIT_INFO['size'][1]):
        for x_idx in range(g.CIRCUIT_INFO['size'][0]):
            if (x_idx,y_idx) in search.keys():
                print(search[(x_idx,y_idx)] + ' '*(2-len(search[(x_idx,y_idx)])),end = ' ')
            else:
                print("-"*2,end = ' ')
        print()
    
    print(f'middle = {middle_point}')
    skip_key = list()
    cross_pare = dict()
    for cnt,pare in sg_list.items():
        for cnt2,pare2 in sg_list.items():
            if cnt < cnt2:
                spos,gpos = pare
                spos2,gpos2 = pare2
                sum = (np.array(spos) + np.array(gpos) + np.array(spos2) + np.array(gpos2))/4
                if sum[0] == middle_point[0] and (spos[1]+gpos[1]) == (spos2[1]+gpos2[1]):
                    
                    if spos[0] < spos2[0]:
                        cross_pare[cnt] = cnt2
                        skip_key.append(cnt2)
                    else:
                        cross_pare[cnt2] = cnt
                        skip_key.append(cnt)

    for key in set(skip_key):
        del sg_list[key]

    pprint.pprint(key_dict)
    pprint.pprint(sg_list)
    print(g.CIRCUIT_INFO['size']+[3])


    # sys.exit()
    """
    numver link solver 使用
    """
    path = solve_numlink(g.CIRCUIT_INFO['size']+[3],sg_list,[])


    """
    結果保存
    """
    new_sg_list = dict()
    path_info = dict()
    new_core = list()
    for key,val in path:
        save_key = key_dict[key]
        path_coords = val[::-1] if temp_save[save_key] == val[::-1] else val
        new_core += path_coords
        path_info[save_key] = path_coords if temp_save[save_key] == path_coords[0] else list(reversed(path_coords))

        if key in cross_pare.keys():
            mirror_path_coords = get_mirror_path(path_coords,middle_point[0])
            save_key = key_dict[cross_pare[key]]
            mirror_path_coords = mirror_path_coords if temp_save[save_key] == mirror_path_coords[0] else list(reversed(mirror_path_coords))
            path_info[save_key] = mirror_path_coords

            if len(set(path_coords) & set(mirror_path_coords)) > 0:
                new_sg_list[key] = [path_coords[0],path_coords[-1]]
                new_sg_list[cross_pare[key]] = [mirror_path_coords[0],mirror_path_coords[-1]]
            else:
                new_core += mirror_path_coords

    print(cross_pare)


    # sys.exit()
    
    """
    cross 配線
    """ 
    
    if new_sg_list != {}:
        new_core = set(new_core)
        for key,pare in new_sg_list.items():
            new_core -= set(pare)

        pprint.pprint(new_sg_list)
        
        path = solve_numlink(g.CIRCUIT_INFO['size']+[3],new_sg_list,new_core)
        for key,val in path:
            save_key = key_dict[key]
            path = val[::-1]
            print(save_key,temp_save[save_key])
            if temp_save[save_key] == tuple(path[0]):
                path_info[save_key] = path
            else:
                path_info[save_key] = path[::-1]

    
    for name,coord in final_coords.items():
        path_info[name] = [coord]

    check_coords = dict()
    for key,value in path_info.items():
        if '-' in key:
            key = key.split('-')
        check_coords[key[0]] = value[0]
        check_coords[key[1]] = value[-1]
        print(key)
        print(value)


    for name,contents in g.DEVICE_INFO.items():
        flg = 0
        print(f'\nname = {name}')
        for what,points in contents['connections2'].items():
            print(what,points)  # -> 
            """
            vss-XM5_S <- で保存されている
            """
            if name + '_' + what in check_coords.keys():
                if int(list(check_coords[name + '_' + what])[1]) != int(points[0][1]):
                    print(f'w = {what}')
                    print(check_coords[name + '_' + what],points)
                    flg = 1
                    break
        if flg == 0:
            g.DEVICE_INFO[name]['conversion'] = False

        else:
            """
            入れ替え
            """
            g.DEVICE_INFO[name]['conversion'] = True

            if 'fet' in g.DEVICE_INFO[name]['type']:
                g.DEVICE_INFO[name]['connections']['G'],g.DEVICE_INFO[name]['connections']['S'] = \
                    g.DEVICE_INFO[name]['connections']['S'],g.DEVICE_INFO[name]['connections']['G']
                g.DEVICE_INFO[name]['connections2']['G'],g.DEVICE_INFO[name]['connections2']['S'] = \
                    g.DEVICE_INFO[name]['connections2']['S'],g.DEVICE_INFO[name]['connections2']['G']
            elif 'res' in g.DEVICE_INFO[name]['type']:
                g.DEVICE_INFO[name]['connections2']['1'],g.DEVICE_INFO[name]['connections2']['2'] = \
                    g.DEVICE_INFO[name]['connections2']['2'],g.DEVICE_INFO[name]['connections2']['1']

    for name,contents in g.DEVICE_INFO.items():
        print(name,contents['conversion'])
    # sys.exit()
    """
    パス保存
    """
    g.CIRCUIT_INFO['path'] = path_info

# 配線箇所を決める
def wiring_points_sub():

    tanshi_coords = dict()
    for name,contents in g.DEVICE_INFO.items():
        """
        改善余地アリ -> 候補座標を増やす
        """
        for what,points in contents['connections2'].items():
            k_point = tuple(points[len(points)//2])
            tanshi_coords[name + '_' + what] = {k_point:points}
    
    final_coords = dict()
    wire_pare = list()
    for node,tanshi_names in g.CIRCUIT_INFO['connect'].items():
        
        tanshi_names = [tanshi_name for tanshi_name in tanshi_names if 'B' not in tanshi_name]
        if len(tanshi_names) == 1 or node in ['vdd','vss']:
            """
            ラベル付ける
            """
            for tanshi_name in tanshi_names:
                coord =  list(tanshi_coords[tanshi_name].keys())[0]
                final_coords[tanshi_name] = tuple(list(coord) + [0])
                final_coords[node+'-'+tanshi_name] = tuple(list(coord) + [0])
        else:
            coords = [list(tanshi_coords[tanshi_name].keys())[0] for tanshi_name in tanshi_names]
            
            connect_pares = list()
            points_pares = list()
            d_set = set()
            grp = set()
            while True:
                """
                配線するノード対を決める
                """
                min_dist = 10000
                min_tanshi_pare = None
                min_coord_pare = None
                idx1 = 0
                for tanshi,coord in zip(tanshi_names,coords):
                    idx1 += 1
                    idx2 = 0
                    for tanshi2,coord2 in zip(tanshi_names,coords):
                        idx2 += 1
                        if idx2 > idx1:
                            tanshi_pare = (tanshi,tanshi2)
                            dist = math.dist(coord,coord2)
                            if dist < min_dist and tanshi_pare not in connect_pares and len(set(tanshi_pare) - grp)>0:
                                min_dist = dist
                                min_tanshi_pare = tanshi_pare
                                min_coord_pare = (coord,coord2)
                
                grp |= set(min_tanshi_pare)
                connect_pares.append(min_tanshi_pare)
                points_pares.append(min_coord_pare)
                d_set.add(min_tanshi_pare[0])
                d_set.add(min_tanshi_pare[1])

                if len(d_set) == len(tanshi_names):
                    break
                
            for cp,pp in zip(connect_pares,points_pares):
                wire_pare.append([cp,pp])

    # solverの準備
    sg_list = dict()
    key_dict = dict()
    temp_save = dict()
    cnt = 0
    
    print(f'middle = {middle_point}')
    """
    配線する座標対を決める
    """
    for tanshis,points in wire_pare:
        tanshi1,tanshi2 = tanshis
        can1 = tanshi_coords[tanshi1][points[0]]
        can2 = tanshi_coords[tanshi2][points[1]]
        min_dist,min_pare = 10000,None
        
        for idx1,p1 in enumerate(can1):
            for idx2,p2 in enumerate(can2):
                dist = math.dist(p1,p2)
                if dist < min_dist:
                    min_dist = dist
                    min_pare = [(p1,p2)]
                elif dist == min_dist:
                    min_pare.append((p1,p2))

        cnt += 1
        s_pos,g_pos = min_pare[len(min_pare)//2]
        sx,sy = int(s_pos[0]),int(s_pos[1])
        gx,gy = int(g_pos[0]),int(g_pos[1])
        sg_list[str(cnt)] = [[sx,sy,0],[gx,gy,0]]

        key_dict[str(cnt)] = tanshis
        temp_save[(tanshi1,tanshi2)] = tuple(sg_list[str(cnt)][0])
        temp_save[(tanshi2,tanshi1)] = tuple(sg_list[str(cnt)][1])

    """
    対称座標対を見つける
    """
    middle_point = ((np.array(g.CIRCUIT_INFO['size'])-1)/2).tolist()
    skip_key = list()
    cross_pare = dict()
    for cnt,pare in sg_list.items():
        for cnt2,pare2 in sg_list.items():
            if cnt < cnt2:
                spos,gpos = pare
                spos2,gpos2 = pare2
                sum = (np.array(spos) + np.array(gpos) + np.array(spos2) + np.array(gpos2))/4
                if sum[0] == middle_point[0] and (spos[1]+gpos[1]) == (spos2[1]+gpos2[1]):
                    cross_pare[cnt] = cnt2
                    skip_key.append(cnt2)
    for key in skip_key:
        del sg_list[key]

    pprint.pprint(key_dict)
    pprint.pprint(sg_list)
    print(g.CIRCUIT_INFO['size']+[3])

    
    """
    numver link solver 使用
    """
    path = solve_numlink(g.CIRCUIT_INFO['size']+[3],sg_list,[])

    """
    結果保存
    """
    new_sg_list = dict()
    path_info = dict()
    new_core = list()
    for key,val in path:
        save_key = key_dict[key]
        path_coords = val[::-1] if temp_save[save_key] == val[::-1] else val
        new_core += path_coords
        path_info[save_key] = path_coords if temp_save[save_key] == path_coords[0] else list(reversed(path_coords))
        if key in cross_pare.keys():
            mirror_path_coords = get_mirror_path(path_coords,middle_point[0])
            save_key = key_dict[cross_pare[key]]
            mirror_path_coords = mirror_path_coords if temp_save[save_key] == mirror_path_coords[0] else list(reversed(mirror_path_coords))
            path_info[save_key] = mirror_path_coords

            if len(set(path_coords) & set(mirror_path_coords)) > 0:
                new_sg_list[key] = [path_coords[0],path_coords[-1]]
                new_sg_list[cross_pare[key]] = [mirror_path_coords[0],mirror_path_coords[-1]]
            else:
                new_core += mirror_path_coords
    
    """
    cross 配線
    """
    if new_sg_list != {}:
        new_core = set(new_core)
        for key,pare in new_sg_list.items():
            new_core -= set(pare)
        
        path = solve_numlink(g.CIRCUIT_INFO['size']+[3],new_sg_list,new_core)
        for key,val in path:
            path_info[key_dict[key]] = val[::-1]


    for name,coord in final_coords.items():
        path_info[name] = [coord]
    """
    for key,value in path_info.items():
        print(key)
        print(value)
    """

    """
    パス保存
    """
    g.CIRCUIT_INFO['path'] = path_info


# 鏡面座標を取得
def get_mirror_position(pos,middle):

    mirror_pos = list(pos)
    add = abs(pos[0] - middle)*2
    mirror_pos[0] = pos[0] if pos[0] == middle else int(pos[0] - add) if pos[0] > middle else int(pos[0] + add)
    mirror_pos = tuple(mirror_pos)

    return mirror_pos

# 鏡面パスを取得
def get_mirror_path(path,middle):
    
    return [get_mirror_position(pos,middle) for pos in path]

if __name__ == '__main__':

    g.DEVICE_INFO = load_json('./temp.json')

    parse_netlist_wire(NETLIST_PATH)

