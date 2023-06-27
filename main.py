

from scripts.magic import *
from scripts.wiring import *
from scripts.compact import *
from scripts.setting import *
import scripts.global_value as g

import pprint,copy

# 準備
def jyunbi():

    g.DEVICE_INFO = dict()

    # 読込 -> ネットリスト
    device_property = parse_netlist(netlist_path = NETLIST_PATH)

    pprint.pprint(device_property)

    for name,property in device_property.items():
        
        # 生成 -> mos
        if 'XM' in name:
            make_mos(name = name,
                    W = property['W'],
                    L = property['L'],
                    M = property['M'],
                    type = property['P'])
        
            # 読込 -> mos
            mag_data = load_mos(mos_name = name)

            # 情報
            width = mag_data['size']['width']
            length = mag_data['size']['height']

            # 生成 -> blk mos
            blk_size,connections = make_block_mos(mos_name=name,\
                                    width=width,height=length,\
                                    connect_point=mag_data['connect'])

        elif 'XR' in name:
            pprint.pprint(property)
            make_res(name = name,
                    W = property['W'],
                    L = property['L'],
                    M = property['M'],
                    type = property['P'])
            
            # 読込 -> res
            res_data = load_res(res_name = name)

            # 情報
            width = res_data['size']['width']
            length = res_data['size']['height']

            # 生成 -> blk res
            blk_size,connections = make_block_res(res_name=name,\
                                    width=width,height=length,\
                                    connect_point=res_data['connect'])

            mag_data = res_data
        
        
        print(f'\nname = {name}')
        print(f'width = {width},length = {length}')
        
        # 保存 -> blk mos
        save_block_mos(mos_name = name,
                    size = blk_size,
                    connect_point=connections,
                    tanshi_info = mag_data['connect'],
                    blk_info = mag_data['blk'])
        
        g.DEVICE_INFO[name] = {'name':name,
                             'type':property['P'],
                             'layout_size':(width,length),
                             'blk_layout_size':tuple(blk_size),
                             'connections':connections}

    # save_json(g.DEVICE_INFO,'./temp.json')

    g.CIRCUIT_INFO = dict()
    parse_netlist_wire(netlist_path = NETLIST_PATH)

    # save_json(g.CIRCUIT_INFO,'./temp2.json')

# 保存
def save_data():

    print("\n" + "#"*20)
    print('SAVE')
    save_data = {"name":g.CIRCUIT_INFO['name'],
                "device":{},
                "kyokai":{},
                "cross":{},
                "size":g.CIRCUIT_INFO['size'],
                "split":None,
                "pin":None,
                'path':{},
                'vdd_connect':list(),
                'vss_connect':list()}
    
    # all_area = [(px, py, 0) for px in range(g.CIRCUIT_INFO['size'][0]) for py in range(g.CIRCUIT_INFO['size'][1])]
    # blk_area = list()
    # device
    for device_name,contents in g.DEVICE_INFO.items():
        
        corner_points = contents['corner_points']
        center_points = contents['center_points']
        blk_layout_size = contents['blk_layout_size']
        type = contents['type']
        con = contents['conversion']

        save_data['device'][device_name] = {"pos":center_points,"corner":corner_points,"size":blk_layout_size,"file_name":type,'conversion':con}

        # blk_area += [(corner_points[0]+dx,corner_points[1]+dy,0) for dx in range(blk_layout_size[0]) for dy in range(blk_layout_size[1])]


    # save_data['mesh'] = list(set(all_area) - set(blk_area))
    # save_data['all'] = all_area

    # pin
    PIN_NAMES = g.CIRCUIT_INFO['pin']
    save_data['pin'] = PIN_NAMES
    
    # path
    path_info = copy.deepcopy(g.CIRCUIT_INFO['path'])
    for key,val in path_info.items():

        print(f'key = {key}')
        print(f'path = {val}')

        if isinstance(key,tuple):
            for label,nodes in g.CIRCUIT_INFO['connect'].items():
                if len(set(nodes) & set(key)) > 0:
                    break
            if len(val) != 0:
                save_data['kyokai'][label] = {"pos":(np.array(val[len(val)//2])+np.array([0,0,val[len(val)//2][-1]+2])).tolist(),"size":[1,1]} 
            else:
                save_data['kyokai'][label] = {"pos":(np.array(val[len(val)//2])+np.array([0,0,1])).tolist(),"size":[1,1]} 
            
            save_data['path'][key[0] + '&' + key[1]] = (np.array(val) + np.array([0,0,2])).tolist()
        elif '-' in key:
            label,tanshi = key.split('-')
            if label in PIN_NAMES:
                save_data['kyokai'][key] = {"pos":(np.array(val[0])+np.array([0,0,1])).tolist(),"size":[1,1]} 

            dn,tn = tanshi.split('_')
            points = g.DEVICE_INFO[dn]['connections2'][tn]
            conversion = g.DEVICE_INFO[dn]['conversion']
            if label in ['vdd','vss']:
                save_data['vdd_connect'].append([label,conversion,points])
        else:
            pass

    # pprint.pprint(save_data['path'])
    # pprint.pprint(save_data['device'])
    # pprint.pprint(save_data['kyokai'])

    save_json(save_data,SAVE_PATH)

"""
メイン?
"""

if __name__ == '__main__':
    
    """
    step 1  準備
    """
    jyunbi()
    # g.DEVICE_INFO = load_json('./temp.json')
    # g.CIRCUIT_INFO = load_json('./temp2.json')
    # pprint.pprint(DEVICE_INFO)

    """
    step 2  配置
    """

    """
    改善余地アリ
    """

    

    
    """
    step 3 圧縮配置　必要なら
    """

    compact_layout(POSITION_PLAN)

    pprint.pprint(g.CIRCUIT_INFO)
    
    """
    step 4  配線
    """
    wiring_points()
    
    """
    step 5  保存
    """
    save_data()

    """
    step 6  レイアウト生成
    """
    make_cir_layout()


    print("\n  !! Complete !!  ")
    print(f'-> {GDS_PATH}')


