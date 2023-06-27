
from pya import *
import re
import json
import sys
import pprint
import numpy as np

class OriginalError(Exception):
    pass

def create_path(cell,index,path,w):

    points = list()
    for pos in path:
        points.append(Point.new(int(pos[0]),int(pos[1])))
    cell.shapes(index).insert(Path.new(points,w))

def create_Box(cell,index,path,w,mode = 0):

    if mode == 0:
      cell.shapes(index).insert(Box.new(path[0][0]-w//2,path[0][1],path[1][0]+w//2,path[1][1]))

      return [[path[0][0]-w//2,path[0][1]],[path[1][0]+w//2,path[1][1]]]
    else:
      cell.shapes(index).insert(Box.new(path[0][0],path[0][1]-w//2,path[1][0],path[1][1]+w//2))

      return [[path[0][0],path[0][1]-w//2],[path[1][0],path[1][1]+w//2]]

    
def create_Box2(cell,index,pos1,pos2):
    
    cell.shapes(index).insert(Box.new(pos1[0],pos1[1],pos2[0],pos2[1]))
    
def create_Box3(cell,index,path,w):

    cell.shapes(index).insert(Box.new(path[0][0],path[0][1]-w//2,path[1][0],path[1][1]+w//2))

def create_dacvia(cell,m_index,via_index,DBU,base_pos,first_l,last_l,mode = 0):


    met_width = 0.4*DBU
    via_width = 0.2*DBU
    via_offset = (met_width-via_width)//2

    if mode == 0:
        count_x = 1
        count_y = 2
    else:
        count_x = 2
        count_y = 1

    # base_pos[0] -= (met_width//2 * count_x)
    # base_pos[1] -= (met_width//2 * count_y)
    
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
"""

def create_dacvia(cell,m_index,via_index,DBU,base_pos,first_l,last_l,mode = 0):

    met_width = 0.4*DBU
    via_width = 0.2*DBU
    via_offset = (met_width-via_width)//2
    
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

"""

if __name__ == '__main__':

    app = Application.instance()
    mw = app.main_window()

    # layoutのcurrent_viewを取得
    try:
        lv = mw.current_view()
        if lv is None:
            raise OriginalError('Cancelled')
    except OriginalError as e:
        print(e)

    # cellの取得
    cell = lv.active_cellview().cell

    # layoutの取得
    layout = cell.layout()
    
    DBU = 1 / cell.layout().dbu

    m1_index = layout.layer(LayerInfo.new(68,20))
    m2_index = layout.layer(LayerInfo.new(69,20))
    m3_index = layout.layer(LayerInfo.new(70,20))
    m4_index = layout.layer(LayerInfo.new(71,20))
    m5_index = layout.layer(LayerInfo.new(72,20))
    m_index = [m1_index,m2_index,m3_index,m4_index,m5_index]
    
    v1_index = layout.layer(LayerInfo.new(68,44))
    v2_index = layout.layer(LayerInfo.new(69,44))
    v3_index = layout.layer(LayerInfo.new(70,44))
    v4_index = layout.layer(LayerInfo.new(71,44))
    v5_index = layout.layer(LayerInfo.new(72,44))
    v_index = [v1_index,v2_index,v3_index,v4_index,v5_index]
    
    capacitor = layout.layer(LayerInfo.new(82,64))

    # 配線幅
    w = 0.14*DBU
    
    # metal width 2
    w2 = 0.28*DBU

    # 配線長さ
    length = 9*DBU

    # 配線間隔
    between = 0.14*DBU
    
    # BIT
    BIT = 5

    # 繰り返し回数
    LOOP = 2**BIT

    RIGHT_POS = None

    LEFT_POS = None

    # 現在の座標
    current_pos_x = current_pos_y = 0
    
    # met_index for capacitor
    cap_index = m2_index
    
    # upper_wire
    hikidashi1 = 0.44*DBU
    
    # under_wire
    hikidashi2 = 0.75*DBU
    
    wire1 = 0.4*DBU
    extend_wire = 1.38*DBU

    # 製造ミスを避けるためのdummyを入れる数
    dummy_met = 4
    
    save_data = dict()
    save_data['root'] = list()
    save_data['d'] = list()
    save_data['d-4'] = list()
    for i in range(BIT+1):
      save_data[str(i)] = list()
      save_data[str(i)+'-4'] = list()
    
    # root_path
    root_wire_width = 0.5*DBU
    subroot_wire_width = 0.3*DBU
    root_length = (w2+w+between*2)*(LOOP+dummy_met)+w2
    
    # 中央の配線
    root_pos = [current_pos_x-w2//2,current_pos_y-root_wire_width//2-hikidashi1]
    path = [root_pos,[root_pos[0]+root_length,root_pos[1]]]
    finish_pos_x =  root_pos[0]+root_length
    create_Box3(cell,cap_index,path,root_wire_width+subroot_wire_width*2)
    ttt = root_wire_width+subroot_wire_width*2
    save_data['root'].append([[path[0][0],path[0][1]-ttt//2],[path[1][0],path[1][1]+ttt//2]])

    RIGHT_POS = [root_pos[0]+root_length+1.8*DBU*(BIT+2),root_pos[1]]

    # 中央配線「角」
    path = [[root_pos[0]+root_length,root_pos[1]],RIGHT_POS]
    create_Box3(cell,cap_index,path,root_wire_width)

    # 中央配線「尾」
    path = [[root_pos[0]-5*DBU,root_pos[1]],[root_pos[0],root_pos[1]]]
    create_Box3(cell,cap_index,path,root_wire_width)
    
    # 接続する配線番号
    wait =['d']
    for i in range(2,BIT+1):
      count = 0     
      for index in range(len(wait)):
        wait.insert(index+count,i)             
        count+=1
    wait = wait + [1] + wait[::-1][1:]
    # print(wait)

    # 接続配線
    connect_count = 0
    connect_met_index = m4_index
    connect_met_width = 0.4*DBU
    connect_met_width2 = 0.4*DBU
    connect_set = set()

    offset_minus = root_wire_width+hikidashi1*2
    
    for count in range(LOOP+dummy_met):
        
        # edge
        if count == 0:
          # 謎のBox箇所
          # 上側
          pos1 = [current_pos_x-w2//2,current_pos_y+length+hikidashi2]
          pos2 = [current_pos_x-w2//2+w*2+w2*2+between*3,current_pos_y+length+hikidashi2+wire1]
          create_Box2(cell,cap_index,pos1,pos2)
          # 下側
          pos1 = [current_pos_x-w2//2,current_pos_y-length-hikidashi2-offset_minus]
          pos2 = [current_pos_x-w2//2+w*2+w2*2+between*3,current_pos_y-length-hikidashi2-wire1-offset_minus]
          create_Box2(cell,cap_index,pos1,pos2)

          # dummy
          path = [[current_pos_x,current_pos_y-hikidashi1],[current_pos_x,current_pos_y+length+hikidashi2]]
          path2 = [[current_pos_x,current_pos_y+hikidashi1-offset_minus],[current_pos_x,current_pos_y-length-hikidashi2-offset_minus]]
        else:
          path = [[current_pos_x,current_pos_y-hikidashi1],[current_pos_x,current_pos_y+length]]
          path2 = [[current_pos_x,current_pos_y+hikidashi1-offset_minus],[current_pos_x,current_pos_y-length-offset_minus]]
        # 端はなぜか追加
        p = create_Box(cell,cap_index,path,w2)
        save_data['root'].append(p)
        p = create_Box(cell,cap_index,path2,w2)
        save_data['root'].append(p)
        
        # center
        current_pos_x += w2//2 + between + w//2
        path = [[current_pos_x,current_pos_y],[current_pos_x,current_pos_y+length+hikidashi2]]
        path2 = [[current_pos_x,current_pos_y-offset_minus],[current_pos_x,current_pos_y-offset_minus-length-hikidashi2]]
        p = create_Box(cell,cap_index,path,w)
        p = create_Box(cell,cap_index,path2,w)
        
        if count > dummy_met//2-1 and count < LOOP+dummy_met//2:
          connect_num = wait[connect_count]
          if connect_num == 'd':
            temp_y = current_pos_y+length+hikidashi2+wire1+extend_wire*(BIT) - 0.01*DBU
            temp2_y = current_pos_y-length-hikidashi2-wire1-extend_wire*(BIT)-offset_minus + 0.01*DBU
          else:
            temp_y = current_pos_y+length+hikidashi2+wire1+extend_wire*(BIT-connect_num) - 0.01*DBU
            temp2_y = current_pos_y-length-hikidashi2-wire1-extend_wire*(BIT-connect_num)-offset_minus + 0.01*DBU
            
            
          path = [[current_pos_x,current_pos_y],[current_pos_x,temp_y]]
          path2 = [[current_pos_x,current_pos_y-offset_minus],[current_pos_x,temp2_y]]
          connect_count+=1
          p = create_Box(cell,cap_index,path,w)
          connect_num_temp = str(0) if connect_num == 'd' else connect_num
          save_data[str(connect_num_temp)].append(p)
          p2 = create_Box(cell,cap_index,path2,w)
          save_data[str(connect_num)].append(p2)
          """
          if connect_num == 'd':
            save_data['0'].append(p)
            save_data['0'].append(p2)
          else:
            save_data[str(connect_num)].append(p)
            save_data[str(connect_num)].append(p2)
          """
          
          create_dacvia(cell,m_index,v_index,DBU,[current_pos_x-0.2*DBU,temp_y],2,4)
          create_dacvia(cell,m_index,v_index,DBU,[current_pos_x-0.2*DBU,temp2_y-0.8*DBU],2,4)
          
          if connect_num not in connect_set:
          
            print(connect_num)
            path = [[current_pos_x-0.2*DBU,temp_y+0.6*DBU],[finish_pos_x+1.5*DBU,temp_y+0.6*DBU]]
            path2 = [[current_pos_x-0.2*DBU,temp2_y-0.6*DBU],[finish_pos_x+1.5*DBU,temp2_y-0.6*DBU]]
            
            print(path)
            print(path2)
            
            p = create_Box(cell,connect_met_index,path,connect_met_width,mode = 1)
            connect_num_temp = str(0) if connect_num == 'd' else connect_num
            save_data[str(connect_num_temp)+'-4'].append(p)
            p = create_Box(cell,connect_met_index,path2,connect_met_width,mode = 1)
            save_data[str(connect_num)+'-4'].append(p)
            create_dacvia(cell,m_index,v_index,DBU,[current_pos_x-0.2*DBU,temp_y],2,4)

            ###########
            ## extend

            # upper
            connect_num_temp = 0 if connect_num == 'd' else connect_num
            path_ext = [path[1],[path[1][0] + (BIT-connect_num_temp) * 1.8 * DBU,path[1][1]]]
            p = create_Box(cell,connect_met_index,path_ext,connect_met_width,mode = 1)
            temp = str(0) if connect_num == 'd' else connect_num
            save_data[str(temp)+'-4'].append(p)

            path_more_ext = [path_ext[1],[RIGHT_POS[0],path_ext[1][1]]]
            p = create_Box(cell,connect_met_index,path_more_ext,connect_met_width,mode = 1)
            temp = str(0) if connect_num == 'd' else connect_num
            save_data[str(temp)+'-4'].append(p)

            via_pos = [path_ext[1][0] - 0.8*DBU, path_ext[1][1]- 0.2*DBU]
            if connect_num != 'd':
              create_dacvia(cell,m_index,v_index,DBU,via_pos,3,4,mode = 1)

            # under
            path2_ext = [path2[1],[path2[1][0] + (BIT-connect_num_temp) * 1.8 * DBU,path2[1][1]]]
            p = create_Box(cell,connect_met_index,path2_ext,connect_met_width,mode = 1)
            save_data[str(connect_num)+'-4'].append(p)
            via_pos2 = [path2_ext[1][0] - 0.8*DBU, path2_ext[1][1]- 0.2*DBU]
            if connect_num != 'd':
              create_dacvia(cell,m_index,v_index,DBU,via_pos2,3,4,mode = 1)
            else:
              upper_pos = [path_ext[1][0]- 0.2*DBU, path_ext[1][1] - (BIT+1)*1.38*DBU]
              under_pos = [path2_ext[1][0]- 0.2*DBU, path2_ext[1][1]]
              p = create_Box(cell,connect_met_index,[upper_pos,under_pos],connect_met_width)
              save_data['d-4'].append(p)
              p = create_Box(cell,connect_met_index,[[upper_pos[0]-0.2*DBU,upper_pos[1]],[RIGHT_POS[0],upper_pos[1]]],connect_met_width,mode = 1)
              save_data['d-4'].append(p)



            if connect_num != 'd':
              ## connect upper under
              upper_pos = [path_ext[1][0]- 0.2*DBU, path_ext[1][1] + 0.2*DBU]
              under_pos = [path2_ext[1][0]- 0.2*DBU, path2_ext[1][1] - 0.2*DBU]
              p = create_Box(cell,m_index[2],[upper_pos,under_pos],connect_met_width)
              save_data[str(connect_num)+'-4'].append(p)

            """
            if connect_num == 'd':
                save_data['0-4'].append([[path[0][0]-connect_met_width//2,path[0][1]],[path[1][0]+connect_met_width//2,path[1][1]]])
                save_data['0-4'].append([[path2[0][0]-connect_met_width//2,path2[0][1]],[path2[1][0]+connect_met_width//2,path2[1][1]]])
            else:
                save_data[str(connect_num)+'-4'].append([[path[0][0]-connect_met_width//2,path[0][1]],[path[1][0]+connect_met_width//2,path[1][1]]])
                save_data[str(connect_num)+'-4'].append([[path2[0][0]-connect_met_width//2,path2[0][1]],[path2[1][0]+connect_met_width//2,path2[1][1]]])
            """
            connect_set.add(connect_num)
          
        # capcitor
        path = [[current_pos_x,current_pos_y-hikidashi1],[current_pos_x,current_pos_y+length]]
        p = create_Box(cell,capacitor,path,w + w2*2 + between*2)
        path2 = [[current_pos_x,current_pos_y+hikidashi1-offset_minus],[current_pos_x,current_pos_y-length-offset_minus]]
        p = create_Box(cell,capacitor,path2,w + w2*2 + between*2)
        
        # edge
        current_pos_x += w//2 + between + w2//2
        if count == LOOP+dummy_met-1:
          pos1 = [current_pos_x-w*2-between*3-w2*3/2,current_pos_y+length+hikidashi2]
          pos2 = [current_pos_x+w2//2,current_pos_y+length+hikidashi2+wire1]
          create_Box2(cell,cap_index,pos1,pos2)
          pos1 = [current_pos_x-w*2-between*3-w2*3/2,current_pos_y-length-hikidashi2-offset_minus]
          pos2 = [current_pos_x+w2//2,current_pos_y-length-hikidashi2-wire1-offset_minus]
          create_Box2(cell,cap_index,pos1,pos2)
          # dummy
          path = [[current_pos_x,current_pos_y-hikidashi1],[current_pos_x,current_pos_y+length+hikidashi2]]
          path2 = [[current_pos_x,current_pos_y+hikidashi1-offset_minus],[current_pos_x,current_pos_y-length-hikidashi2-offset_minus]]
        else:
          path = [[current_pos_x,current_pos_y-hikidashi1],[current_pos_x,current_pos_y+length]]
          path2 = [[current_pos_x,current_pos_y+hikidashi1-offset_minus],[current_pos_x,current_pos_y-length-offset_minus]]
        p = create_Box(cell,cap_index,path,w2)
        save_data['root'].append(p)
        p = create_Box(cell,cap_index,path2,w2)
        save_data['root'].append(p)

    pprint.pprint(save_data)
    print(wait)
    print(save_data.keys())


    """
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
    pprint.pprint(save_data)
    """
# pprint.pprint(save_data)
        
        



