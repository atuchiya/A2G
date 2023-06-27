
import pprint,sys,pprint
import numpy as np
from scripts.setting import *
from scripts.util import *
import scripts.global_value as g

# 圧縮モジュール
def compact_layout(gene):

    """
    初期化
    """
    # サイズ
    NUM_X,NUM_Y = len(gene[0]),len(gene)
    # 1次元に直す
    gene = list(np.array(gene).ravel())

    device_info = {0: [None,(0,0)]}
    cnt = 0
    for name,contents in g.DEVICE_INFO.items():
        cnt += 1
        device_info[cnt] = [name,contents['blk_layout_size']]
    
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
    FreeSpace = list()
    for idx in range(NUM_X*NUM_Y):
        row,column = divmod(idx,NUM_X)
            
        # ブロック番号
        NUM_blk = gene[row * NUM_X + column]
        
        # skip
        if NUM_blk == 0:
            FreeSpace.append((row,column))
            continue
        
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
    
    SPACE_X = 1
    SPACE_Y = 1
    # 空きスペース
    for row,column in FreeSpace:
        target_idx = row * NUM_X + column

        delete_space = (each_area_size[target_idx][0] - SPACE_X) // 2
        delete_space = delete_space if delete_space%2==0 else delete_space-1
        for diff_column in range(1,NUM_X):
            if 0 > column-diff_column or column+diff_column > NUM_X-1:
                break
            
            # 左にあるブロック
            left_blk = gene[row * NUM_X + (column-diff_column)]
            if left_blk == 0:
                break

            # 右にあるブロック
            right_blk = gene[row * NUM_X + (column+diff_column)]
            if right_blk == 0:
                break

            each_area_size[target_idx][0] = SPACE_X
        
        delete_space = (each_area_size[target_idx][1] - SPACE_Y) // 2
        delete_space = delete_space if delete_space%2==0 else delete_space-1
        for diff_row in range(1,NUM_Y):
            if 0 > row-diff_row or row+diff_row > NUM_Y-1:
                break

            # 上にあるブロック
            upper_blk = gene[(row-diff_row) * NUM_X + column]
            if upper_blk == 0:
                break

            # 下にあるブロック
            under_blk = gene[(row+diff_row) * NUM_X + column]
            if under_blk == 0:
                break

            each_area_size[target_idx][1] = SPACE_Y

    # DEBUG 2
    """
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

    position_candidate = [None for _ in range(NUM_X*NUM_Y)]
    for row in range(NUM_Y):
        for column in range(NUM_X):

            idx = row*NUM_X+column
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
            
            position_candidate[idx] = (px,py)
            position_candidate[idx] = (px+column,py+row)
            diff_x = (local_x_size[row] - min(local_x_size))//2
            diff_y = (local_y_size[column] - min(local_y_size))//2
            position_candidate[idx] = (px+column - diff_x,py+row - diff_y)

    # DEBUG 3
    print('\nDEBUG3')
    for y in range(NUM_Y):
        for x in range(NUM_X):
            print(position_candidate[y*NUM_X+x],end = " ")
        print()
    print()


    x_list = list()
    y_list = list()
    for y in range(NUM_Y):
        for x in range(NUM_X):
            idx = y*NUM_X+x
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
    pprint.pprint(each_area_size)
    for y in range(NUM_Y):
        for x in range(NUM_X):
            idx = y*NUM_X+x
            bnum = gene[idx]
            if bnum == 0:
                continue

            name,bsize = device_info[bnum]

            # position area
            cx,cy = position_candidate[idx]
            print(name,cx,cy)
            
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

    









