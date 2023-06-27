
#　ナンバーリンクソルバーの使用

import os
import subprocess
import random
import re
import pprint
import sys
from scripts.util import *
from scripts.setting import *


NumberLink_HOME = './NumberLink'

def zip_out(path):

    ref_info = dict()

    data = load_json(path)

    pos_data = data['pos']

    rot_flag_data = data['rot']

    tanshi_pos_info = data['tanshi']

    max_x = -100
    max_y = -100

    for key,value in tanshi_pos_info.items():

        x0,y0 = value

        if x0 > max_x:
            max_x = x0

        if y0 > max_y:
            max_y = y0

    # print()
    max_x2 = 0
    max_y2 = 0

    for key,value in pos_data.items():

        x0,y0,x1,y1 = value
        # x0 = max_x - x0
        # x1 = max_x - x1
        y0 = max_y - y0 + 1
        y1 = max_y - y1 + 1

        ref_pos = (int(x0)-1,int(y1)-1,0)

        if x1 > max_x2:
            max_x2 = x1-1
        if y0  > max_y2:
            max_y2 = y0-1
        width = x1 - x0
        length = y0 -y1

        # print(f'key = {key},ref = {ref_pos},width = {width},length = {length}')

        ref_info[key] = {'ref':ref_pos,'width':int(width),'length':int(length)}

    # print(f'max_y = {max_y}')
    new_tanshi_pos_info = dict()
    for t,pos in tanshi_pos_info.items():

        px,py = pos[0],max_y - pos[1] + 1
        new_tanshi_pos_info[t] = (px-1, py-1, 0)
        # print(f't = {t},pos = {(pos[0], max_y - pos[1] + 1, 0)}')

        if px > max_x2:
            max_x2 = px-1
        if py > max_y2:
            max_y2 = py-1

    cir_size = [int(max_x2)-1,int(max_y2)-1,3]

    return ref_info,cir_size,rot_flag_data,new_tanshi_pos_info

def prepare_solve(banmen,ini_sg_list,core_list):

    sg_list = []
    count = 0
    for key,item in ini_sg_list.items():
        item[0] = list(item[0])
        item[1] = list(item[1])
        if None in item:
            continue
        if type(key) == tuple:
            key = str(key[0]).zfill(2)+str(key[1]).zfill(2)+str(key[2]).zfill(2)
        elif type(key) == int:
            key = str(key).zfill(6)
        sg_list.append([key,item[0],item[1]])
        count += 1
    

    data = []
    sg_list = sorted(sg_list,key = lambda x: x[0])

    
    size_info = "SIZE "+str(banmen[0])+"X"+str(banmen[1])+"X"+str(banmen[2])
    data.append(size_info)
    linenum_info = "LINE_NUM "+str(count)
    data.append(linenum_info)
    data.append("")
    for sg in sg_list:
        line_info = "LINE#"+sg[0]+" ("+str(sg[1][0])+","+str(sg[1][1])+","+str(sg[1][2]+1)+") ("+str(sg[2][0])+","+str(sg[2][1])+","+str(sg[2][2]+1)+")"
        data.append(line_info)
    
    for core in core_list:
        if core[0] < 0 or core[1] < 0 or core[0] > banmen[0] or core[1] > banmen[1]:
            continue
        core_info = "CORE "+"("+str(core[0])+","+str(core[1])+","+str(core[2]+1)+")"
        data.append(core_info)

    path = NumberLink_HOME + '/num_link_file/test_pynq.txt'

    with open(path,"w") as f:
        for da in data:
            f.write(da)
            f.write('\n')
    
    return sg_list
    
def conv_boardstr(lines, terminals='initial', _seed=12345):
    """
    問題ファイルを boardstr に変換
    """
    #random.seed(_seed)
    random.seed()

    boardstr = ''
    
    for line in lines:
        if 'SIZE' in line:
            x, y, z = line.strip().split(' ')[1].split('X')
            boardstr += ('X%02dY%02dZ%d' % (int(x), int(y), int(z)))
        if 'LINE_NUM' in line:
            pass
        if 'LINE#' in line:
            _line = re.sub(r', +', ',', line)
            _line = re.sub(r' +', ' ', _line)
            sp = _line.strip().replace('-', ' ').replace('(', '').replace(')', '').split(' ')
            #print(sp)

            # s (スタート) -> g (ゴール)
            s_str = sp[1].split(',')
            g_str = sp[2].split(',')
            s_tpl = (int(s_str[0].strip()), int(s_str[1].strip()), int(s_str[2].strip()))
            g_tpl = (int(g_str[0].strip()), int(g_str[1].strip()), int(g_str[2].strip()))

            # 端に近い方をスタートにしたいから各端までの距離計算する
            # (探索のキューを小さくしたいから)
            s_dist_x = min(s_tpl[0], int(x) - 1 - s_tpl[0])
            s_dist_y = min(s_tpl[1], int(y) - 1 - s_tpl[1])
            s_dist_z = min(s_tpl[2], int(z) - 1 - s_tpl[2])
            s_dist = s_dist_x + s_dist_y + s_dist_z
            #print(s_dist_x, s_dist_y, s_dist_z, s_dist)
            g_dist_x = min(g_tpl[0], int(x) - 1 - g_tpl[0])
            g_dist_y = min(g_tpl[1], int(y) - 1 - g_tpl[1])
            g_dist_z = min(g_tpl[2], int(z) - 1 - g_tpl[2])
            g_dist = g_dist_x + g_dist_y + g_dist_z
            #print(g_dist_x, g_dist_y, g_dist_z, g_dist)

            # start と goal
            start_term = '%02d%02d%d' % (int(s_str[0]), int(s_str[1]), int(s_str[2]))
            goal_term  = '%02d%02d%d' % (int(g_str[0]), int(g_str[1]), int(g_str[2]))

            # 端に近い方をスタートにするオプションがオンのときは距離に応じて端点を選択する
            if terminals == 'edgefirst':
                if s_dist <= g_dist:
                    boardstr += ('L' + start_term + goal_term)
                else:
                    boardstr += ('L' + goal_term + start_term)
            # ランダムにスタート・ゴールを選ぶ
            elif terminals == 'random':
                if random.random() < 0.5:
                    boardstr += ('L' + start_term + goal_term)
                else:
                    boardstr += ('L' + goal_term + start_term)
            # 問題ファイルに出てきた順
            else:
                boardstr += ('L' + start_term + goal_term)
        if 'CORE' in line:
            _line = re.sub(r', +', ',', line)
            _line = re.sub(r' +', ' ', _line)
            sp = _line.strip().replace('-', ' ').replace('(', '').replace(')', '').split(' ')
            
            c_str = sp[1].split(',')
            
            c_tpl = (int(c_str[0].strip()), int(c_str[1].strip()), int(c_str[2].strip()) - 1)
            dummy_tpl = (0,0,0)

            core_term = '%02d%02d%d' % (int(c_str[0]), int(c_str[1]), int(c_str[2]))
            dummy_term  = '%02d%02d%d' % (int(dummy_tpl[0]), int(dummy_tpl[1]), int(dummy_tpl[2]))
            boardstr += ('C' + core_term + dummy_term)
            
    return boardstr

def make_boardstr():

    path = NumberLink_HOME + '/num_link_file/test_pynq.txt'

    with open(path, 'r') as f:
        lines = f.readlines()

    # 問題ファイルを boardstr に変換
    # boardstr = BoardStr.conv_boardstr(lines, args.terminals, args.seed)
    boardstr = conv_boardstr(lines, 'initial', 12345)

    return boardstr

def solve_numlink(banmen,ini_sg_list,core_list):

    # ナンバーリンクの回答ファイルを消しておく
    # 回答ファイルが更新されないのを防ぐ
    path_out = NumberLink_HOME + "/num_link_file/result_path.txt"
    path_ans = NumberLink_HOME + "/num_link_file/path_info.txt"
    if os.path.exists(path_out):
        os.remove(path_out)

    sg_list = prepare_solve(banmen,ini_sg_list,core_list)

    boardstr = make_boardstr()

    cmd = [NumberLink_HOME + "/sim",boardstr,path_out,path_ans]

    # 「5」はタイムアウト時間なので値を変更して動作させてみてください
    proc = subprocess.Popen(cmd,stdout=subprocess.PIPE)
    w_time = 1
    
    """
    # Pythonで実行したいプログラムの代わりのループ
    for i in range(w_time): 	# 8の値を変えて実行時間を変えてみてください
        
        time.sleep(1) 	# 1秒待つ
        if proc.poll() is None: 	# Noneのときは子プロセス実行中のとき
            fAlive = True
        else: 	# None以外のとき、子プロセスは終了しています
            fAlive = False
        print(i+1,"秒, 子プロセス実行中 =",fAlive)
    """
    if proc.poll() is None: 	# Noneのときは子プロセス実行中のとき
        fAlive = True
    else: 	# None以外のとき、子プロセスは終了しています
        fAlive = False
    
    # pollで結果は得られていますが、communicateの使い方も示すためコードを含めておきます
    try:
        outs, errs = proc.communicate(timeout=1) 	# timeoutを1秒に設定
        # print("procは正常に終了しています。")
        # print(outs.decode("sjis"))
    except subprocess.TimeoutExpired: 	# タイムアウトしたときここに来ます
        print("procは実行中です。killします。")
        proc.kill() 	# 子プロセスをkillします
        outs, errs = proc.communicate()
        print(outs.decode("sjis"))
        return "false"

    # ナンバーリンク失敗->もう一度
    if boardstr == "false":
        print("======失敗=======")
        return "false"
    try:
        # 結果読み取り
        lines = open_file(path_out)
    except FileNotFoundError:
        print("======失敗=======")
        return "false"


    # 成功の場合
    # 回答読み取り
    if lines[1] == "Test Passed!":
        lines2 = open_file(path_ans)
        path_list = read_answer(lines2,sg_list)
    # 失敗->もう一度
    else:
        print("======不可能======")
        return "false"
        
    random.seed()

    return path_list

def neighbor(pos):
    return [(pos[0]+1,pos[1],pos[2]),(pos[0]-1,pos[1],pos[2]),(pos[0],pos[1]+1,pos[2]),(pos[0],pos[1]-1,pos[2]),(pos[0],pos[1],pos[2]+1),(pos[0],pos[1],pos[2]-1)]

def read_answer(lines,sg_list):

    z = 0
    position_dict = {}
    pattern = 'path*'
    for index,line in enumerate(lines):
        # print(line)
        if re.match(pattern,line):
            num = int(line.split('path')[1])
            
            position_dict[sg_list[num-1][0]] = []
            for i in range(index+1,len(lines)):
                contents = lines[i].split(",")
                if len(contents) == 1:
                    break
                # print(contents)
                x = int(contents[0].split("(")[1])
                y = int(contents[1])
                z = int(contents[2].split(")")[0])
                position_dict[sg_list[num-1][0]].append((x,y,z))
                # contents = [x for x in contents if x]
                # print(contents)
    path_list = []
    for num,path in position_dict.items():
        path_list.append([num,path])

    return path_list





