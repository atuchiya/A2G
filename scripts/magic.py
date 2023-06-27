
import numpy as np
import math,subprocess

from scripts.util import *
from scripts.setting import *
import sys,pprint

"""
command
"""
def exe_magic_file(path = None):

    # pex
    cp = subprocess.run(["magic","-noconsole","-dnull",path])
    print("returncode:", cp.returncode)

"""
読込 -> ネットリスト
"""
def parse_netlist(netlist_path = None):

    lines = read_file(path=netlist_path)
    lines = split_line(lines=lines)

    params = dict()
    for line in lines:
        if '.param' in line:
            name,value = line[1].split('=')
            params[name] = value

    pprint.pprint(params)

    mos_property = dict()
    res_property = dict()
    for idx in range(len(lines)):
        if len(lines[idx]) == 0:
            continue
        # mosfet
        name = lines[idx][0]
        print(name)
        if 'XM' in name:
            mos_property[name] = dict()
            mos_property[name]['C'] = lines[idx][1:5]
            mos_property[name]['P'] = lines[idx][5]
            for word in lines[idx]:
                if 'L=' in word:
                    value = word.split('L=')[1]
                    if value in params.keys():
                        value = params[value]
                    mos_property[name]['L'] = value
                elif 'W=' in word:
                    value = word.split('W=')[1]
                    if value in params.keys():
                        value = params[value]
                    mos_property[name]['W'] = value
            add_idx = 1
            
            while 'XM' not in lines[idx + add_idx][0]:
                add_idx += 1
                if '+' != lines[idx + add_idx][0]:
                    break
                for word in lines[idx + add_idx]:
                    if 'm=' in word:
                        value = word.split('m=')[1]
                        if value in params.keys():
                            value = params[value]
                        mos_property[name]['M'] = value
        # resistor
        if 'XR' in name:
            mos_property[name] = dict()
            mos_property[name]['C'] = lines[idx][1:3]
            mos_property[name]['P'] = lines[idx][4]
            for word in lines[idx]:
                if 'L=' in word:
                    value = word.split('L=')[1]
                    if value in params.keys():
                        value = params[value]
                    mos_property[name]['L'] = value
                elif 'W=' in word:
                    value = word.split('W=')[1]
                    if value in params.keys():
                        value = params[value]
                    mos_property[name]['W'] = value
                elif 'm=' in word:
                    value = word.split('m=')[1]
                    if value in params.keys():
                        value = params[value]
                    mos_property[name]['M'] = value
            add_idx = 1
            while 'XR' not in lines[idx + add_idx][0]:
                add_idx += 1
                if '+' != lines[idx + add_idx][0]:
                    break
                for word in lines[idx + add_idx]:
                    if 'm=' in word:
                        value = word.split('m=')[1]
                        if value in params.keys():
                            value = params[value]
                        mos_property[name]['M'] = value



    pprint.pprint(mos_property)
    return mos_property

"""
生成 -> サブサーキット
"""
def make_cir_layout():

    global SAVE_PATH

    save_data = load_json(SAVE_PATH)
    pin_names = save_data['pin']
    cir_size = save_data['size']
    cir_name = save_data['name']
    device_data = save_data['device']
    path_data = save_data['path']
    kyokai_data = save_data['kyokai']
    # 素子ブロックの占有エリア以外のブロック
    # mesh_data = save_data['mesh']
    # all_data = save_data['all']
    vdd_connect = save_data['vdd_connect']
    vss_connect = save_data['vss_connect']

    lines = read_file(MAGIC_EXPORT)
    t_idx = lines.index('# insert')

    lines.insert(t_idx,' '.join([LAYOUT_HEADER,OUTDIR,cir_name,TECHNOLOGY]))
    t_idx += 1

    device_area = list()
    add_mesh_area = list()

    # device
    for name in device_data.keys():

        mag_data = load_json(MAGIC_HOME + '/save/' + name + '_block.json')

        size_x,size_y = mag_data['size']

        blk_info = np.array(mag_data['blk'])/MAGIC_UNIT/2

        # position
        pos_x,pos_y = device_data[name]['pos']
        pos_x += BLOCKSIZE/2
        pos_y += BLOCKSIZE/2
        off = device_data[name]['size']
        corner = device_data[name]['corner']

        type = device_data[name]['file_name']

        print()
        print("#"*30)
        print(name)
        print(pos_x,pos_y)
        print(size_x,size_y)
        print(blk_info,type)
        print(-1*size_x//2+1,size_x//2+1)
        print(-1*size_y//2+1,size_y//2)
        
        space = size_y - (blk_info[3] - blk_info[1])
        print(f'space = {space}')

        # print([(int(pos_x-BLOCKSIZE/2 + diff_x),int(pos_y-BLOCKSIZE/2+diff_y)) \
        #     for diff_x in range(-1*size_x//2+1,size_x//2+1,1) for diff_y in range(-1*size_y//2+1,size_y//2+1,1)])

        # device_area += [(int(pos_x-BLOCKSIZE/2 + diff_x),int(pos_y-BLOCKSIZE/2+diff_y)) \
        #     for diff_x in range(-1*size_x//2,size_x//2+1,1) for diff_y in range(-1*size_y//2+1,size_y//2+1,1)]

        if space > 1.0:
            device_area += [(corner[0]+dx,corner[1]+dy,0) for dx in range(size_x) for dy in range(size_y)]
        else:
            device_area += [(corner[0]+dx,corner[1]+dy,0) for dx in range(size_x) for dy in range(-1,size_y+1)]

        
        # add_mesh_area += [(int(pos_x-BLOCKSIZE/2 + diff_x),int(pos_y-BLOCKSIZE/2+diff_y)) \
        #     for diff_x in range(-1*size_x//2+1,size_x//2+1,1) for diff_y in [-1*size_y//2+1,size_y//2]]
        
        # conversion
        con = device_data[name]['conversion']
        print(f'con = {con}\n')
        # rotation
        rot = 180
        # rot = device_data[name]['rotation']

        if con == False:
            orientation = 'M0'
        else:
            orientation = 'R180'
        # orientation = 'R0'
        # if con == True:
        #     if rot == 0:
        #         orientation = 'MY'
        #     else:
        #         orientation = 'R180'
        # else:
        #     if rot == 0:
        #         orientation = 'M0'
        #     else:
        #         orientation = 'MX'

        print(orientation)
  
        lines.insert(t_idx,' '.join([INSTANCE_HEADER,name,PCELL_DIR,name,make_coord(coord=[pos_x,pos_y]),orientation,'1 1 0 0']))
        t_idx += 1

        coords = np.array([pos_x,pos_y,pos_x,pos_y])
        device_type = 0 if 'nfet' in type else 1 if 'pfet' or 'res' in type else None
        print(f'=> {device_type}')
        for line in make_blk_connect(device_type = device_type,coords = coords,size_x = size_x,size_y = size_y,blk_info = blk_info):
            lines.insert(t_idx,line)
            t_idx += 1

    # sys.exit()

    path_coords = set()
    # path
    for key,path in path_data.items():

        # label
        label1,label2 = key.split('&')

        if VDD in label1 or VDD in label2:
            continue
        if VSS in label1 or VSS in label2:
            continue

        label1 = label1.split('-')[0]
        label2 = label2.split('-')[0]

        # if label1 == label2:
        #     continue

        path_set = set([tuple([pos[0],pos[1]]) for pos in path])

        ## head
        o_coord = path[0][:2]
        # lines.insert(t_idx,make_pin_for_mag(name = label1,layer = path[0][-1],coord = o_coord))
        # t_idx += 1
        # via
        if 'XM' in label1:
            coord = (np.array(o_coord) + 0.5)
            lines.insert(t_idx,make_via_for_mag(coord = coord,prev_lyr = 1,next_lyr = 2))
            t_idx += 1

        ## foot
        o_coord = path[-1][:2]
        # lines.insert(t_idx,make_pin_for_mag(name = label2,layer = path[-1][-1],coord = o_coord))
        # t_idx += 1
        # via
        if 'XM' in label2.split('-')[0]:
            coord = (np.array(o_coord) + 0.5)
            lines.insert(t_idx,make_via_for_mag(coord = coord,prev_lyr = 1,next_lyr = 2))
            t_idx += 1

        # if len(path_set) == len(path_set & set(device_area)):
        #     continue
        insert_lines,o_coords = make_path_for_mag(path = path)

        # if key == "XM2_D&XM4_G":
        #     sys.exit()


        # if key == 'XMinn_S-XMdiff_D&XMdiff_D-XMinn_S':
        #     sys.exit()
        path_coords |= o_coords
        # path
        for line in insert_lines:
            lines.insert(t_idx,line)
            t_idx += 1

    # print(sorted(list(device_pos_set)))

    # kyokai
    mouokenai = set()
    cnt = 0
    for name,contents in kyokai_data.items():
        coord = contents['pos'][:2]
        layer = contents['pos'][-1]
        name = name.split('-')[0]
        # print(name,coord,layer)
        if name == 'vdd':
            layer = 0
        elif name == 'vss':
            layer = 1
        if tuple(coord) not in mouokenai:
            mouokenai.add(tuple(coord))
        else:
            coord[1] -= 0.05

        if name not in pin_names:
            continue

        cnt += 1
        lines.insert(t_idx,make_pin_for_mag(name = name,layer = layer,coord = coord))
        t_idx += 1

        # name = 'pin1' if layer == 0 else 'pin2' if layer == 1 else 'pin3' if layer == 2 else 'pin4'
        # lines.insert(t_idx,' '.join([INSTANCE_HEADER,name,TEMPLATE_DIR,name,make_coord(coord=[coord[0]+0.5,coord[1]+0.5]),orientation,'1 1 0 0']))
        # t_idx += 1
        # lines.insert(t_idx,' '.join([RECT_HEADER,'M1PIN',make_coords(coords = [[coord[0]-0.5,coord[1]-0.5],[coord[0]+0.5,coord[1]+0.5]])]))
        # print(' '.join([RECT_HEADER,'M1PIN',make_coords(coords = [[coord[0]-0.5,coord[1]-0.5],[coord[0]+0.5,coord[1]+0.5]])]))
        # t_idx += 1


    # mesh
    all_area = [(px, py, 0) for px in range(-1,cir_size[0]+1) for py in range(-1,cir_size[1]+1)]
    for coord in list(set(all_area) - set(device_area)):
        # each coord of empty space
        coord = np.array(coord[:2])

        tonari_blk = {'r':0,'l':0,'t':0,'b':0}
        rcoord = tuple((coord + np.array([1,0])).astype(int))
        if rcoord in device_area:
            tonari_blk['r'] = 1
        lcoord = tuple((coord + np.array([-1,0])).astype(int))
        if lcoord in device_area:
            tonari_blk['l'] = 1
        tcoord = tuple((coord + np.array([0,1])).astype(int))
        if tcoord in device_area:
            tonari_blk['t'] = 1
        bcoord = tuple((coord + np.array([0,-1])).astype(int))
        if bcoord in device_area:
            tonari_blk['b'] = 1

        for line in make_mesh_for_mag(coord=coord,tonari_blk = tonari_blk):
            lines.insert(t_idx,line)
            t_idx += 1

    print(vdd_connect)
    print(vss_connect)
    """ 
    for contents in vdd_connect:
        flg,points = contents
        for idx,point in enumerate(sorted(points)):
            # path = [[point[0]+BLOCKSIZE/2,point[1]+BLOCKSIZE/2,0],[point[0]+BLOCKSIZE/2,point[1]+BLOCKSIZE/2-2,0]]
            # insert_lines = [' '.join([PATH_HEADER,M1,str(LINEWIDTH*MAGIC_UNIT),make_coords(coords=path)])]
            # # path
            # for line in insert_lines:
            #     lines.insert(t_idx,line)
            #     t_idx += 1

            if idx == 0:
                path = [[point[0]+BLOCKSIZE/2,point[1]+BLOCKSIZE/2,0],[point[0]+BLOCKSIZE/2-BLOCKSIZE*2,point[1]+BLOCKSIZE/2,0]]
                insert_lines = [' '.join([PATH_HEADER,M1,str(LINEWIDTH*MAGIC_UNIT),make_coords(coords=path)])]
                # path
                for line in insert_lines:
                    lines.insert(t_idx,line)
                    t_idx += 1
            if idx == len(points)-1:
                path = [[point[0]+BLOCKSIZE/2,point[1]+BLOCKSIZE/2,0],[point[0]+BLOCKSIZE/2+BLOCKSIZE*2,point[1]+BLOCKSIZE/2,0]]
                insert_lines = [' '.join([PATH_HEADER,M1,str(LINEWIDTH*MAGIC_UNIT),make_coords(coords=path)])]
                # path
                for line in insert_lines:
                    lines.insert(t_idx,line)
                    t_idx += 1
    """

    
    for contents in vss_connect+vdd_connect:
        
        which,flg,points = contents
        for point in points:
            if flg:
                offset1 = -1*BLOCKSIZE
                offset2 = -3*BLOCKSIZE
            else:
                offset1 = 1*BLOCKSIZE
                offset2 = 3*BLOCKSIZE

            if which == 'vss':
                path = [[point[0]+BLOCKSIZE/2,point[1]+BLOCKSIZE/2-MESH_SIZE/2+BLOCKSIZE/2,1],[point[0]+BLOCKSIZE/2,point[1]+BLOCKSIZE/2+MESH_SIZE/2-offset2,1]]
                insert_lines = [' '.join([PATH_HEADER,VSS_METAL,str(MESH_SIZE*MAGIC_UNIT),make_coords(coords=path)])]
            elif which == 'vdd':
                path = [[point[0]+BLOCKSIZE/2,point[1]+BLOCKSIZE/2-MESH_SIZE/2,1],[point[0]+BLOCKSIZE/2,point[1]+BLOCKSIZE/2+MESH_SIZE/2-offset1,1]]
                insert_lines = [' '.join([PATH_HEADER,VSS_METAL,str(MESH_SIZE*MAGIC_UNIT),make_coords(coords=path)])]
                insert_lines.append(make_via_for_mag(coord = path[-1],prev_lyr = 0,next_lyr = 1))
                path = [[point[0]+BLOCKSIZE/2,point[1]+BLOCKSIZE/2-offset1,1],[point[0]+BLOCKSIZE/2,point[1]+BLOCKSIZE/2-offset2,1]]
                insert_lines.append(' '.join([PATH_HEADER,VDD_METAL,str(MESH_SIZE*MAGIC_UNIT),make_coords(coords=path)]))
            
            # path
            for line in insert_lines:
                lines.insert(t_idx,line)
                t_idx += 1


    """
    for coord in all_data:
        mode = None
        coord1 = tuple([coord[0],coord[1],2])
        coord2 = tuple([coord[0],coord[1],3])
        if coord1 in path_coords and coord2 in path_coords:
            continue
        elif coord1 in path_coords:
            mode = 'horizon'
        elif coord2 in path_coords:
            mode = 'vertical'
        else:
            mode = 'all'
        # each coord of empty space
        for line in make_dummy_for_mag(coord=coord,mode = mode,path_coords = path_coords):
            lines.insert(t_idx,line)
            t_idx += 1
    """
    # add_lines = ['calma write ./gds/'+cir_name+'.gds',
    #                 'save',
    #                 'feedback find',
    #                 'feedback save ./gds/'+cir_name+'.fb',
    #                 'feedback why',
    #                 'exit']

    add_lines = ['calma write ' + GDS_PATH,
                    'save',
                    'feedback find',
                    'feedback save ./gds/'+cir_name+'.fb',
                    'feedback why',
                    'exit']

    for line in add_lines:
        lines.insert(t_idx,line)
        t_idx += 1

    # make gds
    write_file(path = GDSTCL,lines=lines)
    cp = subprocess.run(["magic","-noconsole","-dnull",GDSTCL])
    print("returncode:", cp.returncode)


"""
magic用座標の作成
"""
def make_coords(coords = None):
    return '{ ' + ' '.join([make_coord(coord=coord) for coord in coords]) + ' } ; '

def make_coord(coord = None):
    coord = np.array(coord)*BLOCKSIZE*MAGIC_UNIT
    coord = coord.astype(int).astype(str)
    return '{ ' + coord[0] + ' ' + coord[1] + ' }'


"""
生成 -> mos gds 
"""
def make_mos(name = None,
            W = None,L = None,M = None,type = None):

    lines = [
        'sky130::'+ type +'_draw {\\',
        'w '+W+' l '+L+' m 1 nf '+M+' \\',
        'full_metal 1 guard 1 glc 1 grc 1 gtc 1 gbc 1 \\',
        'topc 1 botc 0 \\',
        'poverlap 0 doverlap 1 \\',
        'lmin 0.15 wmin 0.42  \\',
        'compatible {sky130_fd_pr__pfet_01v8  \\',
        'sky130_fd_pr__pfet_01v8_lvt \\',
        'sky130_fd_pr__pfet_01v8_hvt  \\',
        'sky130_fd_pr__pfet_g5v0d10v5} \\',
        'diffcov 100 polycov 100 \\',
        'tbcov 100 rlcov 100  \\',
        'viasrc 100 viadrn 100 viagate 100  \\',
        'viagb 0 viagr 0 viagl 0 viagt 0}',
        'save ' + PCELL_DIR + '/' +name + '_origin.mag',
        'cellname rename (UNNAMED) ' + name + '_origin',
        'calma write ' + PCELL_DIR + '/' +name + '_origin.gds',
        'exit',
    ]
    # print(PCELL_DIR + name + '.mag')
    write_file(path = MOSTCL,lines = lines)
    exe_magic_file(path = MOSTCL)
"""
生成 -> res gds 
"""
def make_res(name = None,
            W = None,L = None,M = None,type = None):

    lines = [
        'sky130::'+type+'_draw {\\',
        'w '+W+' l '+L+' m '+M+' nx 1 wmin 0.42 lmin 2.10 \\',
        'rho 120 val 600.0 dummy 0 dw 0.05 term 0.0 \\',
        'sterm 0.0 caplen 0.4 snake 0 guard 1 \\',
        'glc 1 grc 1 gtc 1 gbc 1 roverlap 0 endcov 100 \\',
        'full_metal 1 vias 1 \\',
        'viagb 0 viagt 0 viagl 0 viagr 0}',
        'save ' + PCELL_DIR + '/' +name + '_origin.mag',
        'cellname rename (UNNAMED) ' + name + '_origin',
        'calma write ' + PCELL_DIR + '/' +name + '_origin.gds',
        'exit',
    ]
    # print(PCELL_DIR + name + '.mag')
    write_file(path = MOSTCL,lines = lines)
    exe_magic_file(path = MOSTCL)

"""
読込 -> mos gds 
"""
def load_mos(mos_name = None):

    mag_path = PCELL_DIR + '/' + mos_name + '_origin.mag'

    mos_data = {'connect':list(),'size':dict()}

    # loading origin mag data
    lines = read_file(path=mag_path)

    x_list = list()
    y_list = list()

    # analysis
    data = dict()
    default_data = dict()
    for idx in range(lines.index("<< checkpaint >>"),lines.index("<< properties >>")):
        
        words = lines[idx].split()

        if '<<' in words:
            name = words[1]
            data[name] = list()
            default_data[name] = list()
            cnt = 0
        else:
            p1_x,p1_y,p2_x,p2_y = [int(v) for v in words[1:]]
            default_data[name].append([p1_x,p1_y,p2_x,p2_y])

            if name != 'checkpaint':
                x_list[len(x_list):len(x_list)] = [p1_x, p2_x]
                y_list[len(y_list):len(y_list)] = [p1_y, p2_y]

            c_set = set([(p1_x,p1_y),(p1_x,p2_y),(p2_x,p2_y),(p2_x,p1_y)])

            flg = 0
            for grp_idx in range(len(data[name])):
                if len(data[name][grp_idx][1] & c_set) != 0:
                    data[name][grp_idx][0].append(cnt)
                    data[name][grp_idx][1] |= c_set
                    flg = 1
            if flg == 0:
                data[name].append([[cnt],c_set])
            cnt += 1

    poly_key = 'polycont'
    poly_data = list()
    for pos_idx,coords in data[poly_key]:
        poly_data[len(poly_data):len(poly_data)] = \
            [[sorted(coords)[0][0],sorted(coords)[0][1],sorted(coords)[-1][0],sorted(coords)[-1][1]]]\
            if len(coords) > 8 else [default_data[poly_key][idx] for idx in pos_idx]

    m1_key = 'metal1'
    ds_cnt = 0
    for pos_idx,coords in data[m1_key]:
        new_coords = [[sorted(coords)[0][0],sorted(coords)[0][1],sorted(coords)[-1][0],sorted(coords)[-1][1]]]\
            if len(coords) > 8 else [default_data[m1_key][idx] for idx in pos_idx]

        for value in new_coords:

            middle_point = (int((value[2] + value[0])/2),int((value[3] + value[1])/2))
            if middle_point in [(int((value[2] + value[0])/2),int((value[3] + value[1])/2)) for value in poly_data]:
                what = 'G'
            else:
                ds_cnt += 1
                what = 'S' if ds_cnt % 2 == 0 else 'D'

            width,height = value[2] - value[0], value[3] - value[1]
            mos_data['connect'].append({
                'middle_point':(middle_point[0]/2/MAGIC_UNIT,middle_point[1]/2/MAGIC_UNIT),
                'width':width/2/MAGIC_UNIT,
                'height':height/2/MAGIC_UNIT,
                'what':what
            })
    mos_data['size']['width'] = (max(x_list) - min(x_list))/MAGIC_UNIT/2
    mos_data['size']['height'] = (max(y_list) - min(y_list))/MAGIC_UNIT/2

    # add label
    add_label_to_mag(mag_path=mag_path,connect_point=mos_data['connect'])

    target_key = 'locali'
    coords = list()
    for contents in data[target_key]:
        coords += list(contents[1])

    x_list = sorted([pos[0] for pos in coords])
    y_list = sorted([pos[1] for pos in coords])

    mos_data['blk'] = [x_list[0],y_list[0],x_list[-1],y_list[-1]]

    return mos_data

"""
読込 -> mos gds 
"""
def load_res(res_name = None):

    mag_path = PCELL_DIR + '/' + res_name + '_origin.mag'

    res_data = {'connect':list(),'size':dict()}

    # loading origin mag data
    lines = read_file(path=mag_path)

    x_list = list()
    y_list = list()

    # analysis
    data = dict()
    default_data = dict()
    for idx in range(lines.index("<< checkpaint >>"),lines.index("<< properties >>")):
        
        words = lines[idx].split()

        if '<<' in words:
            name = words[1]
            data[name] = list()
            default_data[name] = list()
            cnt = 0
        else:
            p1_x,p1_y,p2_x,p2_y = [int(v) for v in words[1:]]
            default_data[name].append([p1_x,p1_y,p2_x,p2_y])

            if name != 'checkpaint':
                x_list[len(x_list):len(x_list)] = [p1_x, p2_x]
                y_list[len(y_list):len(y_list)] = [p1_y, p2_y]

            c_set = set([(p1_x,p1_y),(p1_x,p2_y),(p2_x,p2_y),(p2_x,p1_y)])

            flg = 0
            for grp_idx in range(len(data[name])):
                if len(data[name][grp_idx][1] & c_set) != 0:
                    data[name][grp_idx][0].append(cnt)
                    data[name][grp_idx][1] |= c_set
                    flg = 1
            if flg == 0:
                data[name].append([[cnt],c_set])
            cnt += 1

    m1_key = 'metal1'
    cnt = 0
    for pos_idx,coords in data[m1_key]:
        new_coords = [[sorted(coords)[0][0],sorted(coords)[0][1],sorted(coords)[-1][0],sorted(coords)[-1][1]]]\
            if len(coords) > 8 else [default_data[m1_key][idx] for idx in pos_idx]
        cnt += 1
        for value in new_coords:


            middle_point = (int((value[2] + value[0])/2),int((value[3] + value[1])/2))

            print(f'mp = {middle_point}')
            what = None

            width,height = value[2] - value[0], value[3] - value[1]
            res_data['connect'].append({
                'middle_point':(middle_point[0]/2/MAGIC_UNIT,middle_point[1]/2/MAGIC_UNIT),
                'width':width/2/MAGIC_UNIT,
                'height':height/2/MAGIC_UNIT,
                'what':str(cnt)
            })
    res_data['size']['width'] = (max(x_list) - min(x_list))/MAGIC_UNIT/2
    res_data['size']['height'] = (max(y_list) - min(y_list))/MAGIC_UNIT/2

    # add label
    add_label_to_mag(mag_path=mag_path,connect_point=res_data['connect'])

    target_key = 'locali'
    coords = list()
    for contents in data[target_key]:
        coords += list(contents[1])

    x_list = sorted([pos[0] for pos in coords])
    y_list = sorted([pos[1] for pos in coords])

    res_data['blk'] = [x_list[0],y_list[0],x_list[-1],y_list[-1]]

    pprint.pprint(res_data)

    return res_data

"""
生成 -> mos data block version
"""
def make_block_mos(mos_name = None,
                    width = None,height = None,
                    connect_point = None):

    ## get blocksize
    block_x = math.ceil(width)
    diff_block_x = block_x if block_x%2 == 1 else block_x + 1
    BLK_X = block_x//2 if block_x%2 == 1 else (block_x + 1)//2

    block_y = math.ceil(height)
    diff_block_y = block_y if block_y%2 == 1 else block_y + 1
    BLK_Y = block_y//2 if block_y%2 == 1 else (block_y + 1)//2

    diff_blocks = [blk for blk in range(-1*BLK_X,BLK_X+1)]

    ## get connection point by block unit
    metal_conntect = {'D':[],'S':[],'G':[]}
    pprint.pprint(connect_point)
    print(diff_blocks)
    for contents in connect_point:

        # G D S
        what = contents['what']
        # 中心
        middle_px,middle_py = np.array(contents['middle_point'])
        # 長さ
        height = contents['height']

        if what in ['D','S']:

            min_y,max_y = (np.array([middle_py,middle_py]) \
                           + np.array([-height/2-0.32/2,height/2+0.32/2]))

            candidate = [idx for idx in diff_blocks\
                if min_y < (idx*BLOCKSIZE) < max_y]
            print(what,candidate)

            if what == 'D':
                metal_conntect['D'].append([middle_px,0.0])
            elif what == 'S':
                metal_conntect['S'].append([middle_px,candidate[0]])

        elif what in ['G']:
            candidate = sorted([idx for idx in diff_blocks],\
                key = lambda y:abs(y-middle_py))
            metal_conntect['G'].append([middle_px,candidate[0]])

    BLK_CONNECT = dict()
    print()
    print(metal_conntect)
    for name,coords in metal_conntect.items():
        x_list, y_pos = sorted([coord[0] for coord in coords]), coords[0][1]
        print(name,x_list,y_pos)
        BLK_CONNECT[name] = [(idx*BLOCKSIZE,y_pos) for idx in diff_blocks\
            if x_list[0] < (idx*BLOCKSIZE) < x_list[-1]]
        
    if diff_block_x <= 3:
        BLK_CONNECT['D'] = [(-1.0,0.0),(1.0,0.0)]
        BLK_CONNECT['G'] = [(0.0,1.0)]
        BLK_CONNECT['S'] = [(0.0,-1.0)]

    #########################################################################################
    # make block mos
    lines = read_file(MAGIC_EXPORT)

    # create layout
    t_idx = lines.index('# insert')
    lines.insert(t_idx,' '.join([LAYOUT_HEADER,PCELL_DIR,mos_name,TECHNOLOGY]))
    t_idx += 1

    # import instance
    lines.insert(t_idx,' '.join([INSTANCE_HEADER,mos_name,PCELL_DIR,mos_name+'_origin'])+ ' { 0 0 } R0 1 1 0 0')
    t_idx += 1

    # make via and path connection of Drain/Sorce by M2
    off = 0.065
    for name,coords in metal_conntect.items():
        write_coords = list()
        for coord in coords:
            coord = (coord[0],coord[1]+off) if name in ['G'] else coord
            write_coords.append(coord)
            lines.insert(t_idx,make_via_for_mag(coord = coord,prev_lyr = 0,next_lyr = 1))
            t_idx += 1
        lines.insert(t_idx,' '.join([PATH_HEADER,M2,'32',make_coords(coords=write_coords) + ';']))
        t_idx += 1

    # save
    add_lines = ['save '+PCELL_DIR+'/'+mos_name+'.mag',
                'cellname rename (UNNAMED) ' + mos_name,
                'calma write '+PCELL_DIR+'/'+mos_name+'.gds',
                'exit']

    for line in add_lines:
        lines.insert(t_idx,line)
        t_idx += 1

    # make
    write_file(path = GDSTCL,lines = lines)
    exe_magic_file(path = GDSTCL)

    return [diff_block_x,diff_block_y],BLK_CONNECT

"""
生成 -> res data block version
"""
def make_block_res(res_name = None,
                    width = None,height = None,
                    connect_point = None):

    ## get blocksize
    block_x = math.ceil(width)
    diff_block_x = block_x if block_x%2 == 1 else block_x + 1
    BLK_X = block_x//2 if block_x%2 == 1 else (block_x + 1)//2

    block_y = math.ceil(height)
    diff_block_y = block_y if block_y%2 == 1 else block_y + 1
    BLK_Y = block_y//2 if block_y%2 == 1 else (block_y + 1)//2

    ## get connection point by block unit
    metal_conntect = {'1':[],'2':[]}

    for contents in connect_point:

        # G D S
        what = contents['what']
        # 中心
        middle_px,middle_py = np.array(contents['middle_point'])
        # 長さ
        height = contents['height']

        metal_conntect[what].append([middle_px,middle_py])

    BLK_CONNECT = dict()
    for name,coords in metal_conntect.items():
        x_pos, y_pos = coords[0]
        x_pos = x_pos//1
        if y_pos < 0:
            y_pos = math.ceil(y_pos)
        else:
            y_pos = y_pos//1
        BLK_CONNECT[name] = [[x_pos,y_pos]]
    
    #########################################################################################
    # make block mos
    lines = read_file(MAGIC_EXPORT)

    # create layout
    t_idx = lines.index('# insert')
    lines.insert(t_idx,' '.join([LAYOUT_HEADER,PCELL_DIR,res_name,TECHNOLOGY]))
    t_idx += 1

    # import instance
    lines.insert(t_idx,' '.join([INSTANCE_HEADER,res_name,PCELL_DIR,res_name+'_origin'])+ ' { 0 0 } R0 1 1 0 0')
    t_idx += 1

    # make via and path connection of Drain/Sorce by M2
    off = 0.065
    for name,coords in metal_conntect.items():
        write_coords = list()
        for coord in coords:
            coord = (coord[0],coord[1]+off) if name in ['G'] else coord
            write_coords.append(coord)
            lines.insert(t_idx,make_via_for_mag(coord = coord,prev_lyr = 0,next_lyr = 1))
            t_idx += 1
        lines.insert(t_idx,' '.join([PATH_HEADER,M2,'25',make_coords(coords=write_coords) + ';']))
        t_idx += 1

    # save
    add_lines = ['save '+PCELL_DIR+'/'+res_name+'.mag',
                'cellname rename (UNNAMED) ' + res_name,
                'calma write '+PCELL_DIR+'/'+res_name+'.gds',
                'exit']

    for line in add_lines:
        lines.insert(t_idx,line)
        t_idx += 1

    # make
    write_file(path = GDSTCL,lines = lines)
    exe_magic_file(path = GDSTCL)

    return [diff_block_x,diff_block_y],BLK_CONNECT



"""
保存 -> mos data block version
"""
def save_block_mos(mos_name = None,size = None,connect_point = None,tanshi_info = None,blk_info = None):

    SAVE_PATH = MAGIC_HOME + '/save/' + mos_name + '_block.json'

    update_connect_point = dict()
    for key,coords in connect_point.items():
        update_connect_point[mos_name + '_' + key] = [(int(v[0])+size[0]//2,int(v[1])+size[1]//2,0) for v in coords]

    data = {'size':size,'tanshi':update_connect_point,'connect':tanshi_info,'blk':blk_info}

    save_json(data,SAVE_PATH)


"""
ラベル
"""
def add_label_to_mag(mag_path = None,connect_point = None):
    
    ## loading origin mag data
    lines = read_file(path=mag_path)
    ## add label
    tar_idx = lines.index('<< properties >>')
    lines.insert(tar_idx,'<< labels >>')
    for contents in connect_point:
        tar_idx += 1
        x,y = str(int(contents['middle_point'][0]*MAGIC_UNIT*2)),str(int(contents['middle_point'][1]*MAGIC_UNIT*2))
        lines.insert(tar_idx,'flabel metal1 '+x+' '+y+' '+x+' '+y+' 0 FreeSans 240 0 0 0 '+contents['what'])
    ## write file
    write_file(path=mag_path,lines=lines)

"""
ピン
"""
def make_pin_for_mag(name = None,layer = None,coord = None):

    coords = np.array([coord,coord]) + 0.5
    coords = coords + np.array([[-BLOCKSIZE/2,-BLOCKSIZE/2],[BLOCKSIZE/2,BLOCKSIZE/2]])
    layer_metal = M1 if layer == 0 else M2 if layer == 1 else M3 if layer == 2 else M4


    print(f'n = {name},c = {coords},l = {layer_metal}')
    
    return ' '.join([PIN_HEADER,name,layer_metal,make_coords(coords = coords)])

"""
長方形
"""
def make_rect_for_mag(coord = None,layer = None,width = None,height = None):

    # _A2G_generate_rect M2 { { -10.0  -30.0  } { 298.0  30.0  } } ;
    coords = np.array([coord,coord]) + np.array([[-width,-height],[width,height]])/2
    layer_metal = M1 if layer == 0 else M2 if layer == 1 else M3 if layer == 2 else M4

    return ' '.join([RECT_HEADER,layer_metal,make_coords(coords = coords)])

"""
配線
"""
def make_path_for_mag(path = None):

    lines = list()
    # path
    write_path = list()

    before_direction = 'vertical' if path[0][0] == path[1][0] else 'horizon'
    before_direction = 'horizon'

    occupation_coords = set()

    # current coord
    for path_idx,c_coord in enumerate(path):

        # end
        if path_idx == len(path)-1:
            break
        
        # next coord
        n_coord = path[path_idx + 1]

        # direction mode
        # current_direction = before_direction if (c_coord[0] == n_coord[0]) and (c_coord[1] == n_coord[1]) else 'horizon' if c_coord[0] == n_coord[0] else 'vertical'
        current_direction = 'vertical' if c_coord[0] == n_coord[0] else 'horizon'

        print(f'idx = {path_idx} \t{c_coord},{n_coord} \t\t{current_direction}')
        print(f'dir = {current_direction}')

        # current
        cpos_x,cpos_y,clayer = c_coord
        c_coord = np.array([cpos_x,cpos_y]) + 0.5

        # if path_idx == 0 and before_direction == 'vertical':
        if path_idx == 0:
            lines.append(make_rect_for_mag(coord = c_coord,layer = 2,width = 0.5,height = 0.5))
            lines.append(make_via_for_mag(coord=c_coord,prev_lyr=1,next_lyr=2))

        # next
        npos_x,npos_y,nlayer = n_coord
        n_coord = np.array([npos_x,npos_y]) + 0.5

        # write path
        write_path = [c_coord,n_coord]

        occupation_coords |= {(cpos_x,cpos_y,clayer),(npos_x,npos_y,clayer)}
        # layer metal
        lm = M3 if clayer == 2 else M4 if clayer == 3 else M5
        print(write_path)
        lines.append(' '.join([PATH_HEADER,lm,str(LINEWIDTH*MAGIC_UNIT),make_coords(coords=write_path)]))

        if clayer != nlayer:
            lines.append(make_via_for_mag(coord=n_coord,prev_lyr=2,next_lyr=3))
            lines.append(make_rect_for_mag(coord = n_coord,layer = 2,width = 0.5,height = 0.5))

        # if current_direction == 'horizon':

        #     occupation_coords |= {(cpos_x,cpos_y,2),(npos_x,npos_y,2)}
        #     # layer metal
        #     lines.append(' '.join([PATH_HEADER,M3,str(LINEWIDTH*MAGIC_UNIT),make_coords(coords=write_path)]))
        # else:

        #     occupation_coords |= {(cpos_x,cpos_y,3),(npos_x,npos_y,3)}
        #     # layer metal
        #     lines.append(' '.join([PATH_HEADER,M4,str(LINEWIDTH*MAGIC_UNIT),make_coords(coords=write_path)]))

        # if current_direction != before_direction:
        #     print(f'c_coord = {c_coord}')
        #     lines.append(make_rect_for_mag(coord = c_coord,layer = 2,width = 0.5,height = 0.5))
        #     lines.append(make_via_for_mag(coord=c_coord,prev_lyr=2,next_lyr=3))

        before_direction = current_direction

    # if before_direction == 'vertical':
    # if before_direction == 'vertical':
    #     lines.append(make_via_for_mag(coord=n_coord,prev_lyr=2,next_lyr=3))

    lines.append(make_rect_for_mag(coord = n_coord,layer = 2,width = 0.5,height = 0.5))
    lines.append(make_via_for_mag(coord=n_coord,prev_lyr=1,next_lyr=2))

    return lines,occupation_coords

"""
配線
"""
def make_path_for_mag2(path = None):

    lines = list()
    # path
    write_path = list()

    before_direction = 'vertical' if path[0][0] == path[1][0] else 'horizon'
    before_direction = 'horizon'

    occupation_coords = set()

    # current coord
    for path_idx,c_coord in enumerate(path):

        # end
        if path_idx == len(path)-1:
            break
        
        # next coord
        n_coord = path[path_idx + 1]

        # direction mode
        # current_direction = before_direction if (c_coord[0] == n_coord[0]) and (c_coord[1] == n_coord[1]) else 'horizon' if c_coord[0] == n_coord[0] else 'vertical'
        current_direction = 'vertical' if c_coord[0] == n_coord[0] else 'horizon'

        print(f'idx = {path_idx} \t{c_coord},{n_coord} \t\t{current_direction}')
        print(f'dir = {current_direction}')

        # current
        cpos_x,cpos_y,layer = c_coord
        c_coord = np.array([cpos_x,cpos_y]) + 0.5

        # if path_idx == 0 and before_direction == 'vertical':
        if path_idx == 0:
            lines.append(make_rect_for_mag(coord = c_coord,layer = 2,width = 0.5,height = 0.5))
            lines.append(make_via_for_mag(coord=c_coord,prev_lyr=1,next_lyr=2))

        # next
        npos_x,npos_y,layer = n_coord
        n_coord = np.array([npos_x,npos_y]) + 0.5

        # write path
        write_path = [c_coord,n_coord]

        if current_direction == 'horizon':

            occupation_coords |= {(cpos_x,cpos_y,2),(npos_x,npos_y,2)}
            # layer metal
            lines.append(' '.join([PATH_HEADER,M3,str(LINEWIDTH*MAGIC_UNIT),make_coords(coords=write_path)]))
        else:

            occupation_coords |= {(cpos_x,cpos_y,3),(npos_x,npos_y,3)}
            # layer metal
            lines.append(' '.join([PATH_HEADER,M4,str(LINEWIDTH*MAGIC_UNIT),make_coords(coords=write_path)]))

        if current_direction != before_direction:
            print(f'c_coord = {c_coord}')
            lines.append(make_rect_for_mag(coord = c_coord,layer = 2,width = 0.5,height = 0.5))
            lines.append(make_via_for_mag(coord=c_coord,prev_lyr=2,next_lyr=3))

        before_direction = current_direction

    # if before_direction == 'vertical':
    if before_direction == 'vertical':
        lines.append(make_via_for_mag(coord=n_coord,prev_lyr=2,next_lyr=3))

    lines.append(make_rect_for_mag(coord = n_coord,layer = 2,width = 0.5,height = 0.5))
    lines.append(make_via_for_mag(coord=n_coord,prev_lyr=1,next_lyr=2))

    return lines,occupation_coords

"""
ビア
"""
def make_via_for_mag(coord = None,prev_lyr = None,next_lyr = None):

    global VIA_CNT
    
    via = 'via_M1_M2_1' if [prev_lyr,next_lyr] in [[0,1],[1,0]] \
        else 'via_M2_M3_0' if [prev_lyr,next_lyr] in [[1,2],[2,1]] \
        else 'via_M3_M4_0' if [prev_lyr,next_lyr] in [[2,3],[3,2]] \
        else None

    # viali
    if via == None:
        # _A2G_generate_rect M2 { { -10.0  -30.0  } { 298.0  30.0  } } ;    
        coords = np.array([coord,coord]) + np.array([[-VIA0_SIZE,-VIA0_SIZE],[VIA0_SIZE,VIA0_SIZE]])/2
        return ' '.join([RECT_HEADER,VIA0,make_coords(coords = coords)])

    VIA_CNT += 1
    return ' '.join([INSTANCE_HEADER,'NoName_'+str(VIA_CNT),TEMPLATE_DIR,via,make_coord(coord=coord),'R0 1 1 0 0',';'])

"""
メッシュ
"""
def make_mesh_for_mag(coord = None,tonari_blk = None):

    lines = list()

    A = np.array(
        [coord,
        coord]
    )

    # ブロックの中心
    A = A + BLOCKSIZE/2

    # x方向
    # normal
    if tonari_blk['r'] == 0 and tonari_blk['l'] == 0:
        B = np.array(
                [[-1 * BLOCKSIZE/2, -1 * MESH_SIZE/2],
                [BLOCKSIZE/2, MESH_SIZE/2]]
            )
    # left
    elif tonari_blk['r'] == 0 and tonari_blk['l'] == 1:
        B = np.array(
                [[-1 * MESH_SIZE/2, -1 * MESH_SIZE/2],
                [BLOCKSIZE/2, MESH_SIZE/2]]
            )
    # right
    elif tonari_blk['r'] == 1 and tonari_blk['l'] == 0:
        B = np.array(
                [[-1 * BLOCKSIZE/2, -1 * MESH_SIZE/2],
                [MESH_SIZE/2, MESH_SIZE/2]]
            )
    # right and left
    else:
        B = np.array(
                [[-1 * MESH_SIZE/2, -1 * MESH_SIZE/2],
                [MESH_SIZE/2, MESH_SIZE/2]]
            )
    lines.append(' '.join([RECT_HEADER,M1,make_coords(coords = A+B),';']))
    lines.append(' '.join([RECT_HEADER,M2,make_coords(coords = A+B),';']))
    
    # y方向　入れ替え
    # normal
    if tonari_blk['t'] == 0 and tonari_blk['b'] == 0:
        B = np.array(
                [[-1 * MESH_SIZE/2, -1 * BLOCKSIZE/2],
                [MESH_SIZE/2, BLOCKSIZE/2]]
            )
    # bottom
    elif tonari_blk['t'] == 0 and tonari_blk['b'] == 1:
        B = np.array(
                [[-1 * MESH_SIZE/2, -1 * MESH_SIZE/2],
                [MESH_SIZE/2, BLOCKSIZE/2]]
            )
    # top
    elif tonari_blk['t'] == 1 and tonari_blk['b'] == 0:
        B = np.array(
                [[-1 * MESH_SIZE/2, -1 * BLOCKSIZE/2],
                [MESH_SIZE/2, MESH_SIZE/2]]
            )
    # top and bottom
    else:
        B = np.array(
                [[-1 * MESH_SIZE/2, -1 * MESH_SIZE/2],
                [MESH_SIZE/2, MESH_SIZE/2]]
            )
    
    lines.append(' '.join([RECT_HEADER,M1,make_coords(coords = A+B),';']))
    lines.append(' '.join([RECT_HEADER,M2,make_coords(coords = A+B),';']))

    return lines

"""
ダミー
"""
def make_dummy_for_mag(coord = None,mode = None,path_coords = None):

    lines = list()

    A = np.array(
        [coord[:2],
        coord[:2]]
    )

    # ブロックの中心
    A = A + BLOCKSIZE/2

    # X方向のrect
    if mode in ['all','horizon']:

        coord1 = np.array([coord[0],coord[1],3])
        coord_l = tuple(coord1 + np.array([-1,0,0]))
        coord_r = tuple(coord1 + np.array([1,0,0]))
        if coord_l in path_coords and coord_r in path_coords:
            B = np.array(
                [[-1 * DUMMY_WIDTH/2, -1 * DUMMY_WIDTH/2],
                [DUMMY_WIDTH/2, DUMMY_WIDTH/2]]
            )
        elif coord_l in path_coords:
            B = np.array(
                [[-1 * DUMMY_WIDTH/2, -1 * DUMMY_WIDTH/2],
                [BLOCKSIZE/2, DUMMY_WIDTH/2]]
            )
        elif coord_r in path_coords:
            B = np.array(
                [[-1 * BLOCKSIZE/2, -1 * DUMMY_WIDTH/2],
                [DUMMY_WIDTH/2, DUMMY_WIDTH/2]]
            )
        else:
            B = np.array(
                [[-1 * BLOCKSIZE/2, -1 * DUMMY_WIDTH/2],
                [BLOCKSIZE/2, DUMMY_WIDTH/2]]
            )
        lines.append(' '.join([RECT_HEADER,M4,make_coords(coords = A + B)]))

    # y方向のrect
    if mode in ['all','vertical']:

        coord1 = np.array([coord[0],coord[1],2])
        coord_d = tuple(coord1 + np.array([0,-1,0]))
        coord_u = tuple(coord1 + np.array([0,1,0]))
        if coord_d in path_coords and coord_u in path_coords:
            C = np.array(
                [[-1*DUMMY_WIDTH/2, -1*DUMMY_WIDTH/2],
                [DUMMY_WIDTH/2, DUMMY_WIDTH/2]]
            )
        elif coord_d in path_coords:
            C = np.array(
                [[-1*DUMMY_WIDTH/2, -1*DUMMY_WIDTH/2],
                [DUMMY_WIDTH/2, BLOCKSIZE/2]]
            )
        elif coord_u in path_coords:
            C = np.array(
                [[-1*DUMMY_WIDTH/2, -1*BLOCKSIZE/2],
                [DUMMY_WIDTH/2, DUMMY_WIDTH/2]]
            )
        else:
            C = np.array(
                [[-1*DUMMY_WIDTH/2, -1*BLOCKSIZE/2],
                [DUMMY_WIDTH/2, BLOCKSIZE/2]]
            )
        lines.append(' '.join([RECT_HEADER,M3,make_coords(coords = A + C)]))

    return lines

"""
バックゲート
"""
def make_blk_connect(device_type = None,coords = None,size_x = None,size_y = None,blk_info = None):

    lines = list()

    # 端ブロックの位置更新
    side_diff = np.array(blk_info) + np.array([VIA0_SIZE/2,VIA0_SIZE,-VIA0_SIZE/2,-VIA0_SIZE])
    
    # 素子ブロック配置位置の端
    side_l,side_d,side_r,side_u = coords + side_diff

    out_lblk,out_dblk,out_rblk,out_ublk = coords + np.array([-1*(size_x//2+1),-1*(size_y//2),size_x//2+1,size_y//2])

    left_info = [side_l,side_d,side_u,out_lblk]
    right_info = [side_r,side_d,side_u,out_rblk]
    down_info = [side_d,side_l,side_r,out_dblk]
    upper_info = [side_u,side_l,side_r,out_ublk]

    # connect
    candidate_block_xpos = [(n+1/2) for n in range(1,50,1) if side_l < (n+1/2) < side_r]
    candidate_block_ypos = [(n+1/2) for n in range(1,50,1) if side_d < (n+1/2) < side_u]

    def my_round(val, digit=0):
        p = 10 ** digit
        return (val * p * 2 + 1) // 2 / p
    
    # device_type = 0 (nmos) or 1 (pmos)
    for idx,info in enumerate([left_info,right_info]):

        info = [my_round(v,5) for v in info]

        # left/right or down/upper ?
        which_side = 1 if idx < 2 else 0

        # 配線幅
        diff_x = np.array([[-1*LINEWIDTH/2,0],[LINEWIDTH/2,0]]) if which_side == 1 else np.array([[0,-1*LINEWIDTH/2],[0,LINEWIDTH/2]])
        diff_y = np.array([[0,-1*MESH_SIZE/2],[0,MESH_SIZE/2]]) if which_side == 1 else np.array([[-1*MESH_SIZE/2,0],[MESH_SIZE/2,0]])

        # 外側ブロック
        candidate_block_pos = candidate_block_ypos if which_side == 1 else candidate_block_xpos

        side_base,side_minus,side_plus,out_blk = info

        # メタルをひく
        metal_coords = [[side_base,side_minus],[side_base,side_plus]] if which_side == 1 \
            else [[side_minus,side_base],[side_plus,side_base]]
        
        lines.append(' '.join([RECT_HEADER,M1,\
            make_coords(coords = np.array(sorted(metal_coords)) + diff_x)]))
        # nmos
        if device_type == 0:
            lines.append(' '.join([RECT_HEADER,M2,\
                make_coords(coords = np.array(sorted(metal_coords)) + diff_x)]))

        # メッシュに接続
        METAL = M1 if device_type == 1 else M2
        for block_pos in candidate_block_pos:
            metal_coords = [[out_blk,block_pos],[side_base,block_pos]] if which_side == 1 \
                else [[block_pos,out_blk],[block_pos,side_base]]
            lines.append(' '.join([RECT_HEADER,METAL,\
                make_coords(coords = np.array(sorted(metal_coords)) + diff_y)]))

        # via
        # 中心ポイント
        xy_point = (side_plus + side_minus) / 2
        for idx,info in enumerate([[VIA0_SIZE,VIA0_SPACE,-1,0],[VIA1_SIZE,VIA1_SPACE,0,1]]):
            if device_type == 1 and idx == 1:
                continue
            via_size,via_space,plyr,nlyr = info
            # 個数
            via_num = (side_plus - side_minus) // (via_size + via_space)
            # viaの配置間隔
            diff = (via_size + via_space) / 2
            if via_num%2 == 1:
                coord = [side_base,xy_point] if which_side == 1 else [xy_point,side_base]
                lines.append(make_via_for_mag(coord = coord,prev_lyr = plyr,next_lyr = nlyr))
            for n in range(int(via_num//2)):
                n = 2*n+2 if via_num%2==1 else 2*n+1
                coord = [side_base,xy_point+diff*n] if which_side == 1 else [xy_point+diff*n,side_base]
                lines.append(make_via_for_mag(coord = coord,prev_lyr = plyr,next_lyr = nlyr))
                coord = [side_base,xy_point-diff*n] if which_side == 1 else [xy_point-diff*n,side_base]
                lines.append(make_via_for_mag(coord = coord,prev_lyr = plyr,next_lyr = nlyr))

    # sys.exit()
    return lines



