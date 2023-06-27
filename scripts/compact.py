
import pprint,sys,pprint
import numpy as np
from scripts.setting import *
from scripts.util import *
import scripts.global_value as g

# 圧縮モジュール
def compact_layout(position):

    """
    初期化
    """
    
    device_info = {0: [None,(0,0)]}
    cnt = 0
    reverse = {0:0}
    for name,contents in g.DEVICE_INFO.items():
        cnt += 1
        device_info[cnt] = [name,contents['blk_layout_size']]
        reverse[name] = cnt

    gene = [[reverse[name] for name in temp] for temp in position]
    
    # サイズ
    NUM_X,NUM_Y = len(gene[0]),len(gene)
    # 1次元に直す
    gene = list(np.array(gene).ravel())

    
    # 素子ブロックの配置座標
    blk_coordinates = dict()
    blk_coordinates['X'] = dict()
    blk_coordinates['Y'] = dict()

    # 初期化
    for idx in range(NUM_X):
        blk_coordinates['X'][idx] = 0
    for idx in range(NUM_Y):
        blk_coordinates['Y'][idx] = 0

    print('\n size')
    print(NUM_X,NUM_Y)
    print('\n device_info')
    pprint.pprint(device_info)


    # 行列
    each_area_size = [[0,0] for _ in range(NUM_X) for _ in range(NUM_Y)]
    check_box = {'X':list(),'Y':list()}
    FreeSpace = list()
    for idx in range(NUM_X*NUM_Y):
        row,column = divmod(idx,NUM_X)
            
        # ブロック番号
        NUM_blk = gene[row * NUM_X + column]
        
        # check
        if NUM_blk == 0:
            FreeSpace.append((row,column))
            if 0 < column < NUM_X-1:
                left_idx = row * NUM_X + (column-1)
                right_idx = row * NUM_X + (column+1)
                if gene[left_idx] != 0 and gene[right_idx] != 0:
                    check_box['Y'].append([idx,left_idx])
            if 0 < row < NUM_Y-1:
                upper_idx = (row+1) * NUM_X + column
                under_idx = (row-1) * NUM_X + column
                if gene[upper_idx] != 0 and gene[under_idx] != 0:
                    check_box['X'].append([idx,upper_idx])
            
        else:
            # デバイスの名前，大きさ
            DEVICE_NAME,DEVICE_SIZE = device_info[NUM_blk]

            # 更新
            if DEVICE_SIZE[0] > blk_coordinates['X'][column]:
                blk_coordinates['X'][column] = DEVICE_SIZE[0]
            if DEVICE_SIZE[1] > blk_coordinates['Y'][row]:
                # 上下がフリースペースの場合，スキップ
                if 0 < row < NUM_Y-1 and \
                    gene[(row-1) * NUM_X + column] == 0 and gene[(row +1)* NUM_X + column] == 0:
                    continue
                blk_coordinates['Y'][row] = DEVICE_SIZE[1]

            if DEVICE_SIZE[0] > each_area_size[idx][0]:
                each_area_size[idx][0] = DEVICE_SIZE[0]
            if DEVICE_SIZE[1] > each_area_size[idx][1]:
                # 上下がフリースペースの場合，スキップ
                if 0 < row < NUM_Y-1 and \
                    gene[(row-1) * NUM_X + column] == 0 and gene[(row +1)* NUM_X + column] == 0:
                    continue
                each_area_size[idx][1] = DEVICE_SIZE[1]

    for idx,ref_idx in check_box['X']:
        each_area_size[idx][0] = each_area_size[ref_idx][0]+1
    for idx,ref_idx in check_box['Y']:
        each_area_size[idx][0] = 1
        each_area_size[idx][1] = each_area_size[ref_idx][1]+1
    # print(each_area_size)
    # each_area_size = [(0,0) for _ in range(NUM_X) for _ in range(NUM_Y)]
    # for idx in range(NUM_X*NUM_Y):
    #     row,column = divmod(idx,NUM_X)
    #     each_area_size[idx] = [blk_coordinates['X'][column],blk_coordinates['Y'][row]]
    # print(each_area_size)
    # sys.exit()
    # DEBUG 1
    
    print('\nDEBUG1')
    for y in range(NUM_Y):
        for x in range(NUM_X):
            print(each_area_size[y*NUM_X+x],end = " ")
        print()
    print()

    
    """
    # DEBUG 2
    print('\nDEBUG2')
    for y in range(NUM_Y):
        for x in range(NUM_X):
            print(each_area_size[y*NUM_X+x],end = " ")
        print()
    print()
    """
    local_x_size = list()
    local_y_size = [0 for _ in range(NUM_X)]
    for y in range(NUM_Y):
        local_x = 0
        for x in range(NUM_X):
            local_x += each_area_size[y*NUM_X+x][0]
            local_y_size[x] += each_area_size[y*NUM_X+x][1]
        local_x_size.append(local_x)

    print(local_x_size)
    print(local_y_size)

    position_candidate = [None for _ in range(NUM_X*NUM_Y)]
    for idx in range(NUM_X*NUM_Y):
        row,column = divmod(idx,NUM_X)

        px = (max(local_x_size) - local_x_size[row])//2
        py = (max(local_y_size) - local_y_size[column])//2

        px,py = 0,0

        if column == 0:
            px += 0
        else:
            for local_column in range(column):
                px += each_area_size[row*NUM_X+local_column][0]
        if row == 0:
            py += 0
        else:
            for local_row in range(row):
                py += each_area_size[local_row*NUM_X+column][1]
        print()
        print((row,column))
        print(px,py)
        
        # offset_x = column if px != 0 else 0
        # offset_y = row if py != 0 else 0

        offset_x = column
        offset_y = row

        position_candidate[idx] = (px,py)
        position_candidate[idx] = (px+offset_x,py+offset_y)
        diff_x = (local_x_size[row] - min(local_x_size))//2
        diff_y = (local_y_size[column] - min(local_y_size))//2
        position_candidate[idx] = (px+offset_x - diff_x,py+offset_y - diff_y)

    # DEBUG 3
    print('\nDEBUG3')
    for y in range(NUM_Y):
        for x in range(NUM_X):
            print(position_candidate[y*NUM_X+x],end = " ")
        print()
    print()

    x_list = list()
    y_list = list()
    for idx in range(NUM_X*NUM_Y):
        bnum = gene[idx]
        if bnum == 0:
            continue

        name,bsize = device_info[bnum]
        # position area
        cx,cy = position_candidate[idx]
        cx = cx + (each_area_size[idx][0] - bsize[0])//2
        cy = cy + (each_area_size[idx][1] - bsize[1])//2
        cx2,cy2 = cx+bsize[0],cy+bsize[1]

        print(name,bsize,cx,cy)

        x_list += [cx,cx2]
        y_list += [cy,cy2]

    min_x,max_x = min(x_list)-1,max(x_list)+1
    min_y,max_y = min(y_list)-1,max(y_list)+1
    
    debug_save = dict()
    for y in range(NUM_Y):
        for x in range(NUM_X):
            idx = y*NUM_X+x
            bnum = gene[idx]
            if bnum == 0:
                continue

            name,bsize = device_info[bnum]
            print(name,bsize)
            pprint.pprint(g.DEVICE_INFO[name])

            # position area
            cx,cy = position_candidate[idx]
            
            # DEVICE_INFO[name]['position_area'] = (cx,cy)

            # corner points
            cx = cx + (each_area_size[idx][0] - bsize[0])//2
            cy = cy + (each_area_size[idx][1] - bsize[1])//2

            cx -= min_x
            cy -= min_y
            g.DEVICE_INFO[name]['corner_points'] = (cx,cy)

            # center points
            px = cx + bsize[0]//2
            py = cy + bsize[1]//2 
            g.DEVICE_INFO[name]['center_points'] = (px,py)

            # plus offset
            g.DEVICE_INFO[name]['connections2'] = dict()
            tt_points = list()
            for t_name,t_points in g.DEVICE_INFO[name]['connections'].items():
                print(t_name,t_points)

                t_points = (np.array(t_points) + np.array([px,py])).tolist()
                g.DEVICE_INFO[name]['connections2'][t_name] = t_points
                tt_points += t_points

            for lx in range(bsize[0]):
                for ly in range(bsize[1]):
                    if (cx+lx,cy+ly) in [(px,py) for px,py in tt_points]:
                        continue
                    debug_save[(cx+lx,cy+ly)] = bnum
    LAYOUT_SIZE = [
        max_x - min_x,
        max_y - min_y
    ]

    g.CIRCUIT_INFO['size'] = LAYOUT_SIZE
    
    for py in range(LAYOUT_SIZE[1]):
        py = LAYOUT_SIZE[1] - py - 1
        for px in range(LAYOUT_SIZE[0]):
            if (px,py) in debug_save.keys():
                print(str(debug_save[(px,py)]).zfill(2), end = ' ')
            else:
                print('  ', end = ' ')
        print()
    print()


# DEBUG
def print_device_info():

    for name,contents in g.DEVICE_INFO.items():

        print()
        print("#"*20)
        for key,value in contents.items():
            print(f'\n{key}')
            if key == 'connections' or key == 'connections2':
                for tanshi,points in value.items():
                    print(tanshi,points)
            else:
                pprint.pprint(value)


if __name__ == '__main__':
    """
    DEVICE_INFO = {0: [None,(0,0)],
            1: ['vss', (1, 1)],
            2: ['vdd', (1, 1)],
            3: ['clk', (1, 1)],
            4: ['outp', (1, 1)],
            5: ['vp', (1, 1)],
            6: ['outn', (1, 1)],
            7: ['vn', (1, 1)],
            8: ['XMdiff', (9, 5)],
            9: ['XMinn', (9, 7)],
            10: ['XMinp', (9, 7)],
            11: ['XMl4', (9, 5)],
            12: ['XMl3', (9, 5)],
            13: ['XM3', (7, 5)],
            14: ['XM2', (7, 5)],
            15: ['XMl1', (7, 5)],
            16: ['XMl2', (7, 5)],
            17: ['XC',(7,15)]}

    gene = [[0,  6,  2,  4,  0],\
            [0, 14,  0, 13,  0],\
            [17, 12,  0, 11, 0],\
            [0, 15,  0, 16,  0],\
            [0,  9,  0, 10,  0],\
            [0,  0,  8,  0,  0],\
            [0,  0,  3,  0,  0],\
            [0,  7,  1,  5,  0]]
    
    base_device_info = dict()
    device_info = {0: [None,(0,0)]}
    cnt = 0
    for name,contents in base_device_info.items():
        cnt += 1
        device_info[cnt] = [name,contents['blk_layout_size']]
    """

    DEVICE_INFO = load_json('./temp.json')
    
    device_info = {0: [None,(0,0)]}
    cnt = 0
    for name,contents in DEVICE_INFO.items():
        cnt += 1
        device_info[cnt] = [name,contents['blk_layout_size']]

    gene = [
        [2,0,4],
        [1,0,3],
        [0,5,0]
    ]

    # 圧縮
    compact_layout(gene,device_info)

    print_device_info()

    









