
import json,math

# loading json data
def load_json(path):
    # jsonデータをdictでload
    data = None
    try:
        with open(path,mode = "r") as fr:
            data = json.load(fr)
    except FileNotFoundError:
        data = dict()
    return data

# saving json format
def save_json(data_dict,save_path):

    # dictをjsonで保存
    with open(save_path,"w") as f:
        data_json = json.dumps(data_dict)
        f.write(data_json)

# write
def write_file(path = None,lines = None):
    with open(path,'w') as f:
        for line in lines:
            f.write(line + '\n')

# read
def read_file(path = None):
    with open(path,'r') as f:
        s = f.read()
    lines = s.split('\n')
    return lines

def open_file(file_path):

    # ファイル読み込み
    with open(file_path,"r") as f:
        s = f.read()
    lines = s.split("\n")

    return lines

# split
def split_line(lines=None):
    for i in range(len(lines)):
        lines[i] = lines[i].split()
    return lines


def euclidean_distance(coord1, coord2):
    return abs(coord1[0] - coord2[0]) + abs(coord1[1] - coord2[1])
    return math.sqrt((coord1[0] - coord2[0])**2 + (coord1[1] - coord2[1])**2)

def find_min_distance_pair(coords1, coords2):
    min_distance = float("inf")
    min_distance_pair = None

    for idx,coord1 in enumerate(coords1):
        for idx2,coord2 in enumerate(coords2):
            if idx < idx2 and coords1 == coords2:
                continue
            distance = euclidean_distance(coord1, coord2)
            if distance < min_distance:
                min_distance = distance
                min_distance_pair = [(coord1, coord2)]
            elif distance == min_distance:
                min_distance_pair.append((coord1, coord2))
    
    min_distance_pair = sorted(min_distance_pair,key=lambda x:x[0][1]+x[1][1],reverse=True)[0]
    # print(min_distance_pair)

    return min_distance_pair, min_distance, (idx,idx2)