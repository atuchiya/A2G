# read design
echo
echo LOADING GDS
gds read $::env(GDS_FILE)
load $::env(CELL_NAME)

# extract for LVS
echo 
echo LVS START
extract all
extract do all
#########################
extresist tolerance 0.1
extresist all
extresist simplify on
extresist lumped on
extresist silent on
extresist skip
extresist extout on
extresist help
#########################
ext2spice lvs
ext2spice subcircuits off
ext2spice -o $::env(LVS_FILE)
echo $::env(LVS_FILE)
echo LVS FINISH!!

echo 
echo PEX START
# extract for PEX
select top cell
port makeall
extract all
extract do all
#########################
ext2sim run
ext2sim rthresh 0.1
ext2sim cthresh 0.01
ext2sim extresist on

#########################
extresist tolerance 0.1
extresist all
extresist simplify on
extresist lumped on
extresist silent on
extresist skip
extresist extout on
extresist help
#########################
# ext2spice lvs
# ext2spice short resistor
ext2spice subcircuit on
ext2spice resistor tee on
ext2spice cthresh 0.001
# ext2spice cthresh infinite
ext2spice rthresh 0.001
ext2spice subcircuit on
ext2spice ngspice
ext2spice -o $::env(PEX_FILE)
echo PEX FINISH!!
echo 

# quit
quit
