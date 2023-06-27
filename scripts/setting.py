import os

TECHNOLOGY = 'sky130A'

LAYOUT_HEADER = '_A2G_create_layout'
INSTANCE_HEADER = '_A2G_generate_instance'
PATH_HEADER = '_A2G_generate_path'
RECT_HEADER = '_A2G_generate_rect'
PIN_HEADER = '_A2G_generate_pin'

HOME = os.getcwd()
MAGIC_HOME = HOME + '/magic'
MAGIC_LAYOUT_DIR = MAGIC_HOME + '/magic_layout'
PCELL_DIR = MAGIC_LAYOUT_DIR + '/pcell'
TEMPLATE_DIR = MAGIC_LAYOUT_DIR + '/skywater130_microtemplates_dense'
MAGIC_EXPORT = MAGIC_HOME + '/magic_export.tcl'


## ここを変える
# netlist
CELLNAME = "diff2sin"
# CELLNAME = "hyscomp"
# CELLNAME = 'comparator'

# diff_sin
POSITION_PLAN = [
    ['XM2',0,'XM4'],
    ['XM1','XM5','XM3'],
    [0,0,0]
]
"""
# comparator
POSITION_PLAN = [
    ['XM2','XMl3',0,'XMl4','XM3'],
    ['XMl1','XMinn',0,'XMinp','XMl2'],
    [0,0,'XMdiff',0,0]
]

# hyscomp
POSITION_PLAN = [
    [0,'XM4','XM6','XM2',0],
    ['XR1',0,0,0,'XR2'],
    [0,'XM1','XM5','XM3',0]
]
"""
##

NETLIST_PATH = HOME + "/netlist/"+CELLNAME+".spice"

# output gds path
GDS_PATH = HOME + "/gds/"+CELLNAME+".gds"
# GDS_PATH = HOME + "/A2G/GPT/gds/fjhiuoaerhfguoir.gds"

# save block data
SAVE_PATH = HOME+'/block_data/'+CELLNAME+'.json'

MOSTCL = MAGIC_HOME + '/temp.tcl'
GDSTCL = MAGIC_HOME + '/make_gds.tcl'

OUTDIR = MAGIC_LAYOUT_DIR
OUTFILE = 'test' # ?

# metal name
M1 = 'M1'
M2 = 'M2'
M3 = 'M3'
M4 = 'M4'
M5 = 'M5'

# voltage
VDD = 'vdd'
VSS = 'vss'

# magic意味わからん
MAGIC_UNIT = 100

BLOCKSIZE = 1.0 # ブロックサイズ

DUMMY_WIDTH = 0.4
LINEWIDTH = 0.4 # 配線の太さ

# local inter connect
VIA_CNT = 0
VIA0 = 'viali'
VIA0_SIZE = 0.17 
VIA0_SPACE = 0.19
VIA1_SIZE = 0.32
VIA1_SPACE = 0.32

# 電源メッシュ
MESH_SIZE = 0.5 # メッシュの太さ
VDD_METAL = M1
VSS_METAL = M2
