
from pya import *
import re
import json
import numpy as n
import pprint
import sys

# pathの作成
def create_path(cell,index,path,w):

    points = list()
    for pos in path:
        points.append(Point.new(int(pos[0]),int(pos[1])))
    cell.shapes(index).insert(Path.new(points,w))

# path型の箱作成
def create_Box(cell,index,path,bsize,w,axis = 0):

    global DBU

    bsize *= DBU
    w *= DBU
    path = n.array(path)*DBU

    # y方向
    if axis == 0:
        path = path + n.array([bsize//2,0])
        cell.shapes(index).insert(Box.new(round(path[0][0]-w//2,0),round(path[0][1],0),round(path[-1][0]+w//2,0),round(path[-1][1]+bsize,0)))
        return [[round(path[0][0]-w//2,0),round(path[0][1],0)],[round(path[-1][0]+w//2,0),round(path[-1][1]+bsize,0)]]
    
    # x方向
    else:
        path = path + n.array([bsize//2-w//2,bsize//2])
        cell.shapes(index).insert(Box.new(round(path[0][0],0),round(path[0][1]-w//2,0),round(path[-1][0]+bsize,0),round(path[-1][1]+w//2,0)))
        return [[round(path[0][0],0),round(path[0][1]-w//2,0)],[round(path[-1][0]+bsize,0),round(path[-1][1]+w//2,0)]]

# 箱作成
def create_Box2(cell,index,pos1,pos2):
    
    cell.shapes(index).insert(Box.new(pos1[0],pos1[1],pos2[0],pos2[1]))

    return [pos1,pos2]

def create_Box3(cell,index,pos,w,h):
    
    cell.shapes(index).insert(Box.new(pos[0],pos[1],pos[0]+w,pos[1]+h))

# text
def create_Text(cell,index,string,pos1,pos2):

    cell.shapes(index).insert(Text.new(string,pos1,pos2))
   
# via作成
def create_dacvia(cell,m_index,via_index,base_pos,first_l,last_l,mode = 0):

    global DBU

    met_width = 0.4*DBU
    via_width = 0.2*DBU
    via_offset = (met_width-via_width)//2

    if mode == 0:
        count_x = 1
        count_y = 2
    else:
        count_x = 2
        count_y = 1

    base_pos[0] -= (met_width//2 * count_x)
    base_pos[1] -= (met_width//2 * count_y)
    
    for l in range(first_l,last_l+1):
    
      create_Box2(cell,m_index[l-1],base_pos,[base_pos[0]+met_width*count_x,base_pos[1]+met_width*count_y])
            
      if l != last_l:
        current_y = base_pos[1]

        for y in range(count_y):
          current_x = base_pos[0]
          for x in range(count_x):
            via_pos_x,via_pos_y = current_x+via_offset,current_y+via_offset
            create_Box2(cell,via_index[l-1],[via_pos_x,via_pos_y],[via_pos_x+via_width,via_pos_y+via_width])
            if x != count_x-1:
              current_x = current_x+met_width
          current_y = current_y+met_width

# 埋め尽くしブロック
def create_tile(cell,bsize,m_index,base_pos):
    global DBU
    bsize *= DBU
    create_Box2(cell,m_index,base_pos,[int(base_pos[0]+bsize),int(base_pos[1]+bsize)])

# 真ん中スタート
def create_direction(cell,bsize,m_index,pos,w,direction='left'):
    global DBU

    bsize *= DBU
    pos = n.array(pos)*DBU
    w *= DBU

    if direction == 'left':
        box = [round(pos[0],0),round(pos[1]+bsize//2-w//2,0)],[round(pos[0]+bsize//2,0),round(pos[1]+bsize//2+w//2,0)]
        
    elif direction == 'right':
        box = [round(pos[0]+bsize),round(pos[1]+bsize//2-w//2,0)],[round(pos[0]+bsize//2,0),round(pos[1]+bsize//2+w//2,0)]
    elif direction == 'upper':
        box = [round(pos[0]+bsize//2-w//2,0),round(pos[1]+bsize//2,0)],[round(pos[0]+bsize//2+w//2,0),round(pos[1]+bsize,0)]
    elif direction == 'under':
        box = [round(pos[0]+bsize//2-w//2,0),round(pos[1],0)],[round(pos[0]+bsize//2+w//2,0),round(pos[1]+bsize//2,0)]

    
    p = create_Box2(cell,m_index,box[0],box[1])
    return p

def create_dacvia(cell,m_index,via_index,base_pos,first_l,last_l,bs):

    global DBU

    bs *= DBU
    met_width = 0.4*DBU
    via_width = 0.2*DBU
    via_offset = (met_width-via_width)//2

    base_pos = [base_pos[0]+bs//2-met_width//2,base_pos[1]+bs-met_width]
    
    count_x = 1
    count_y = 2

    for l in range(first_l,last_l+1):
    
      create_Box2(cell,m_index[l-1],base_pos,[base_pos[0]+met_width*count_x,base_pos[1]+met_width*count_y])
            
      if l != last_l:
        current_y = base_pos[1]

        for y in range(count_y):
          current_x = base_pos[0]
          for x in range(count_x):
            via_pos_x,via_pos_y = current_x+via_offset,current_y+via_offset
            create_Box2(cell,via_index[l-1],[via_pos_x,via_pos_y],[via_pos_x+via_width,via_pos_y+via_width])
            if x != count_x-1:
              current_x = current_x+met_width
          current_y = current_y+met_width

def make_subcell(name):

    global TOP_CELL
    global DBU
    global LAYOUT
    global NAME_LIST

    if name not in NAME_LIST.keys():

        # subcell
        sub_cell = LAYOUT.create_cell(name)
        inst = CellInstArray.new(sub_cell.cell_index(),Trans.new(0, 0))
        TOP_CELL.insert(inst)
        NAME_LIST[name] = sub_cell
    
    else:

        # subcell
        TOP_CELL.copy_instances(NAME_LIST[name])

        sub_cell = NAME_LIST[name]

    return sub_cell


if __name__ == '__main__':

    # お決まりのパターン
    app = Application.instance()
    mw = app.main_window()

    # layoutのcurrent_viewを取得
    try:
        lv = mw.current_view()
        if lv is None:
            raise OriginalError('Cancelled')
    except OriginalError as e:
        print(e)

    ################################################
    ## global 変数

    # cellの取得
    TOP_CELL = lv.active_cellview().cell

    # DBUの取得
    DBU = 1 / TOP_CELL.layout().dbu

    # layoutの取得
    LAYOUT = TOP_CELL.layout()

    NAME_LIST = dict()
    ################################################

    ################################################
    # 各layerのindexを取得
    m1_index = LAYOUT.layer(LayerInfo.new(68,20))
    m2_index = LAYOUT.layer(LayerInfo.new(69,20))
    m3_index = LAYOUT.layer(LayerInfo.new(70,20))
    m4_index = LAYOUT.layer(LayerInfo.new(71,20))
    m5_index = LAYOUT.layer(LayerInfo.new(72,20))
    m_index = [m1_index,m2_index,m3_index,m4_index,m5_index]
    
    v1_index = LAYOUT.layer(LayerInfo.new(68,44))
    v2_index = LAYOUT.layer(LayerInfo.new(69,44))
    v3_index = LAYOUT.layer(LayerInfo.new(70,44))
    v4_index = LAYOUT.layer(LayerInfo.new(71,44))
    v5_index = LAYOUT.layer(LayerInfo.new(72,44))
    v_index = [v1_index,v2_index,v3_index,v4_index,v5_index]

    capacitor_index = LAYOUT.layer(LayerInfo.new(82,64))
    ################################################

    ################################################
    ## 設定
    fname = 'cdac'
    bsize = 0.3

    save_path = '/home/oe23ranan/block/gui/skywater/'+fname+'/out_'+fname+'_'+str(bsize)+'.json'
    
    # ブロックサイズの決定
    bsize = 0.4
    # 容量を作るための配線長さ（平行方向に重なる長さ）
    L = 9

    # 配線間距離
    between = 0.14
    
    # 配線幅
    lw = round((bsize-between)*2/3,2)

    # 容量を作るための配線を構成するブロック数
    ynum = int(round((L-bsize/2)/bsize,0))

    between_flag = 0
    
    # 配線幅がブロックサイズを超えたとき
    # 一つの配線幅をブロックサイズに設定する
    if lw*2 > bsize:
        between_flag = 1
        temp = (bsize-lw)/2
        L = temp * 10 / between
        ynum = int(round((L-bsize/2)/bsize,0))

    bit = 4

    # 繰り返し回数
    loop = 2**bit

    # 接続する配線番号
    wait =['d']
    for i in range(2,bit+1):
      count = 0     
      for index in range(len(wait)):
        wait.insert(index+count,i)             
        count+=1
    wait = wait + [1] + wait[::-1][1:]

    print()
    print('#'*20)
    print('config list')

    print(f'block size = {bsize}')
    print(f'line width = {lw}')
    print(f'between flag = {between_flag}')
    print(f'bit = {bit}, loop = {loop}')
    print(f'wait = {wait}')

    print('#'*20)
    print()


    ################################################

    cir_data = dict()
    with open(save_path,mode = 'r') as fr:
        cir_data = json.load(fr)

    path_data = cir_data['path']

    layer_path = dict()
    via1 = list()
    via2 = list()

    for key,path in path_data.items():
        current_z = None
        temp = list()
        for index,pos in enumerate(path):
            pos = [round(pos[0]*bsize,3),round(pos[1]*bsize,3),pos[2]]
            
            # 階層が同じ場合
            if current_z == pos[2]:
                temp.append(pos[:2])
            # 階層が変わる場合
            else:
                # via1を経由する場合
                if (current_z == 0 and pos[2] == 1) or (current_z == 1 and pos[2] == 0):
                    
                    via1.append([pos[:2],abs(pos[0]-path_data[key][index+1][0])])
                # via2を経由する場合
                elif (current_z == 1 and pos[2] == 2) or (current_z == 2 and pos[2] == 1):
                    via2.append([pos[:2],abs(pos[0]-path_data[key][index+1][0])])

                # これまでのpathを保存 
                if len(temp) != 0:
                    # 階層ごとに保存
                    if current_z not in layer_path.keys():
                        layer_path[current_z] = [temp]
                    else:
                        layer_path[current_z].append(temp)
                
                current_z = pos[2]
                temp = [pos[:2]]
            current_x = pos[0]

        if temp[0] > temp[-1]:
            temp.reverse()

        if current_z not in layer_path.keys():
            layer_path[current_z] = [temp]
        else:
            layer_path[current_z].append(temp)
    
    print()
    print('#'*20)
    print('path')
    print()
    for key,value in layer_path.items():
        print(f'key = {key}')
        for index,path in enumerate(value):
            print(f'index = {index}')
            print(path)
            print()
    print('#'*20)
    print()

    save_data = dict()
    save_data['root'] = list()
    save_data['d'] = list()
    save_data['d-4'] = list()
    for i in range(bit+1):
      save_data[str(i)] = list()
      save_data[str(i)+'-4'] = list()

    last_pos = None
    loop_path = list()
    for key,value in layer_path.items():
        for index,path in enumerate(value):
            # root
            if 0 <= index <= 2:
                
                last_pos = path[0][0]+bsize*2*loop
                path[-1] = [path[0][0]+bsize*2*loop,path[0][1]]
                # p = create_Box(TOP_CELL,m_index[1],path,bsize,bsize,axis = 1)
                # save_data['root'].append(p)
                # path = n.array(path)*[1,-1]
                # p = create_Box(cell,m_index[1],path,bsize,bsize,axis = 1)
                # save_data['root'].append(p)

            elif index <= 5:
                path = [[path[0][0],round(path[0][1]+diff*bsize,2)] for diff in range(ynum+1)]
                loop_path.append(path)

    count = 0
    all_count = 0
    already = set()
    current_node = str(wait[all_count])
    for l in range(loop):

        # １個の容量
        capacitor_positions_p = list()
        capacitor_positions_n = list()

        # p_cap_cell = make_subcell("cap")
        # n_cap_cell = make_subcell("cap")

        p_cap_cell = make_subcell("cap"+str(current_node))
        n_cap_cell = make_subcell("cap"+str(current_node))

        for index,path in enumerate(loop_path):
            
            # root
            if index % 2 == 0:
                # 横にずらして配置
                path = list(n.array(path) + [round(bsize*2*l,3),0])

                # lw > bs
                if between_flag == 1:
                    # positive
                    p_path = path
                    metal = m_index[1]
                    p = create_Box(p_cap_cell,metal,p_path,bsize,bsize,axis = 0)
                    # capcacitor
                    if index == 0:
                        temp = p[0]
                        temp[1] -= bsize*DBU
                        capacitor_positions_p.append(temp)
                    elif index == 2:
                        capacitor_positions_p.append(p[-1])
                    # negative
                    n_path = list(n.array(p_path) * [1,-1] + n.array([0,bsize*2]))
                    n_path.reverse()
                    metal = m_index[1]
                    p2 = create_Box(n_cap_cell,metal,n_path,bsize,bsize,axis = 0)
                    # capcacitor
                    if index == 0:
                        capacitor_positions_n.append(p2[0])
                       
                    elif index == 2:
                        temp = p2[-1]
                        capacitor_positions_n.append(temp)
                        
                # lw < bs
                else:
                    # positive
                    p_path = path
                    metal = m_index[1]
                    p = create_Box(p_cap_cell,metal,p_path,bsize,lw*2,axis = 0)
                    # capcacitor
                    if index == 0:
                        temp = p[0]
                        temp[1] -= bsize*DBU
                        capacitor_positions_p.append(temp)
                    elif index == 2:
                        capacitor_positions_p.append(p[-1])
                    # negative
                    # n_path = list(n.array(path) * [1,-1] + n.array([0,path[0][1]]))
                    n_path = list(n.array(path) * [1,-1] + n.array([0,bsize*2]))
                    n_path.reverse()
                    metal = m_index[1]
                    p2 = create_Box(n_cap_cell,metal,n_path,bsize,lw*2,axis = 0)
                    # capcacitor
                    if index == 0:
                        capacitor_positions_n.append(p2[0])
                    elif index == 2:
                        temp = p2[-1]
                        capacitor_positions_n.append(temp)

                if index == 2:
                    # positive
                    temp = create_Box2(p_cap_cell,capacitor_index,capacitor_positions_p[0],capacitor_positions_p[1])
                    temp = create_Box2(p_cap_cell,m_index[1],capacitor_positions_p[0],[capacitor_positions_p[1][0],capacitor_positions_p[0][1]+bsize*DBU])
                    save_data['root'].append(temp)
                    # negative
                    # temp = create_Box2(n_cap_cell,capacitor_index,capacitor_positions_n[0],capacitor_positions_n[1])
                    temp = create_Box2(n_cap_cell,capacitor_index,capacitor_positions_n[0],[capacitor_positions_n[1][0],capacitor_positions_n[1][1]+bsize*DBU])
                    temp = create_Box2(n_cap_cell,m_index[1],[capacitor_positions_n[0][0],capacitor_positions_n[1][1]],[capacitor_positions_n[1][0],capacitor_positions_n[1][1]+bsize*DBU])
                    save_data['root'].append(temp)
                save_data['root'].append(p)
                save_data['root'].append(p2)
            # side
            else:
                path.sort()
                # 横にずらす
                path = list(n.array(path) + [round(bsize*2*l,3),0])

                dummy_flag = 0
                if wait[all_count] == 'd':
                    wait[all_count] = 0
                    dummy_flag = 1
                
                flag = 0
                if wait[all_count] not in already:
                    already.add(wait[all_count])
                    flag = 1

                # 容量
                # positive
                p = create_direction(p_cap_cell,bsize,m_index[1],path[0],lw,'upper')
                save_data[str(wait[all_count])].append(p)
                # negative
                p = create_direction(n_cap_cell,bsize,m_index[1],list(n.array(path[0])*[1,-1]+[0,bsize*2]),lw,'under')
                save_data[str(wait[all_count])].append(p)

                extend = [[path[-1][0],round(path[-1][1]+bsize*n,3)+bsize] for n in range(3+(bit-wait[all_count])*4)]

                new_path = path[1:] + extend
                
                # positive
                p_path = path[1:]
                p = create_Box(p_cap_cell,m_index[1],p_path,bsize,lw,axis = 0)
                save_data[str(wait[all_count])].append(p)
                # negative
                path = list(reversed(path[1:]))
                n_path = n.array(path)*[1,-1]+n.array([0,bsize*2])
                p = create_Box(n_cap_cell,m_index[1],n_path,bsize,lw,axis = 0)
                save_data[str(wait[all_count])].append(p)

                ## 引き出し線
                # positive
                p = create_Box(TOP_CELL,m_index[1],extend,bsize,lw,axis = 0)
                save_data[str(wait[all_count])].append(p)

                # negative
                temp = list(reversed(extend))
                p = create_Box(TOP_CELL,m_index[1],n.array(temp)*[1,-1]+[0,bsize*2],bsize,lw,axis = 0)
                save_data[str(wait[all_count])].append(p)

                ## via
                via_pos = new_path[-1]
                # positive
                via_pos = list(n.array(via_pos) * DBU)
                create_dacvia(TOP_CELL,m_index,v_index,via_pos,2,4,bsize)
                # negative
                via_pos = list(n.array(via_pos)*[1,-1]+[0,bsize*DBU])
                create_dacvia(TOP_CELL,m_index,v_index,via_pos,2,4,bsize)

                #####################################################################################
                # 横方向の引き出し線
                if flag == 1:
                    path = [new_path[-1],[last_pos,new_path[-1][1]]]
                    path = n.array(path) + [0,bsize]
                    p = create_Box(TOP_CELL,m_index[3],path,bsize,0.4,axis = 1)

                    save_data[str(wait[all_count])+'-4'].append(p)

                    edge = bsize*(4 + 3*(bit-wait[all_count]))

                    # 上側飛び出し配線
                    temp = list(path)+[[path[-1][0]+bsize*30,path[-1][1]]]
                    p = create_Box(TOP_CELL,m_index[3],temp,bsize,0.4,axis = 1)
                    save_data[str(wait[all_count])+'-4'].append(p)

                    pos = temp[-1][0]*DBU,temp[-1][1]*DBU
                    create_Text(TOP_CELL,LAYOUT.layer(LayerInfo.new(71,5)),"n"+str(wait[all_count]),pos[0],pos[1])
                    create_Box3(TOP_CELL,LAYOUT.layer(LayerInfo.new(71,16)),pos,0.4*DBU,0.4*DBU)

                    positive_edge = [path[-1][0]+edge,path[-1][1]-bsize]

                    if wait[all_count] != 0:
                        via_pos = list(n.array(positive_edge) * DBU)
                        create_dacvia(TOP_CELL,m_index,v_index,via_pos,3,4,bsize)

                    # negative
                    
                    path = n.array(path) *[1,-1]+[0,bsize*2]
                    path = list(path)
                    temp = list(reversed(list(path)))
                    p = create_Box(TOP_CELL,m_index[3],temp,bsize,0.4,axis = 1)
                    save_data[str(wait[all_count])+'-4'].append(p)


                    temp = [temp[0]] + [[temp[0][0]+edge,temp[0][1]]]
                    
                    p = create_Box(TOP_CELL,m_index[3],temp,bsize,0.4,axis = 1)
                    save_data[str(wait[all_count])+'-4'].append(p)

                    negative_edge = [path[-1][0]+edge,path[-1][1]]

                    if wait[all_count] != 0:
                        via_pos = list(n.array(negative_edge) * DBU)
                        create_dacvia(TOP_CELL,m_index,v_index,via_pos,3,4,bsize)

                    # 上としたをつなげる
                    if wait[all_count] != 0:
                        p = create_Box(TOP_CELL,m_index[2],[positive_edge,negative_edge],bsize,0.4,axis = 1)
                        save_data[str(wait[all_count])+'-4'].append(p)
                    else:
                        p = create_Box(TOP_CELL,m_index[3],[[positive_edge[0],bsize*25],negative_edge],bsize,0.4,axis = 0)
                        save_data[str(wait[all_count])+'-4'].append(p)
                        p = create_Box(TOP_CELL,m_index[3],[[positive_edge[0],bsize*24],[path[-1][0]+bsize*30,bsize*24]],bsize,0.4,axis = 0)
                        save_data[str(wait[all_count])+'-4'].append(p)
                        temp = [path[-1][0]+bsize*30,bsize*24]
                        pos = temp[0]*DBU,temp[1]*DBU
                        create_Text(TOP_CELL,LAYOUT.layer(LayerInfo.new(71,5)),"ndum",pos[0],pos[1])
                        create_Box3(TOP_CELL,LAYOUT.layer(LayerInfo.new(71,16)),pos,0.4*DBU,0.4*DBU)
                #####################################################################################

                all_count += 1

                if all_count > len(wait)-1:
                    continue

                print(f'current_node = {current_node}')
                current_node = wait[all_count]
                if dummy_flag == 1 and current_node == 0:
                    current_node = 'd'
        
        count += 1

    p = create_Box(TOP_CELL,m_index[1],[[-12*bsize,bsize],[path[-1][0]+bsize*30,bsize]],bsize,0.4,axis = 0)
    save_data['d'] = list()
    remove = list()
    for index in range(len(save_data['0'])):
        contents = save_data['0'][index]
        if contents[0][1] < 0:
            save_data['d'].append(contents)
            remove.append(contents)
    for r in remove:
        save_data['0'].remove(r)

    save_data['d-4'] = list()
    remove = list()
    for index in range(len(save_data['0-4'])):
        contents = save_data['0-4'][index]
        if contents[0][1] < 0:
            save_data['d-4'].append(contents)
            remove.append(contents)

    for r in remove:
        save_data['0-4'].remove(r)
        
    

    with open("/home/oe23ranan/block/cdac_"+str(bit)+"_"+str(bsize)+".json","w") as f:
        data_json = json.dumps(save_data)
        f.write(data_json)  

    w = 0.01
    w*=DBU

    cir_size = [loop*2+1,40]
    """
    for x in range(cir_size[0]+1):
        points = [[x*bsize,0],[x*bsize,cir_size[1]*bsize]]
        points=n.array(points)*DBU
        a1 = []
        for p in points:
            a1.append(Point.new(int(p[0]), int(p[1])))
        cell.shapes(m_index[key]).insert(Path.new(a1,w))

    for y in range(cir_size[1]+1):
        points = [[0,y*bsize],[cir_size[0]*bsize,y*bsize]]
        points=n.array(points)*DBU
        a1 = []
        for p in points:
            a1.append(Point.new(int(p[0]), int(p[1])))
        cell.shapes(m_index[key]).insert(Path.new(a1,w))
    """
    