
export PDKPATH=/tmp/caravel_tutorial/pdk/volare/sky130/versions/7519dfb04400f224f140749cda44ee7de6f5e095/sky130A
# export PDKPATH=/tmp/caravel_tutorial/pdk/sky130A
export SKYWATER=/tmp/caravel_tutorial/pdk/skywater-pdk/

# copy over RC file
# cp $PDKPATH/libs.tech/magic/sky130A.magicrc .magicrc


CURRENT=$(cd $(dirname $0);pwd)
echo $CURRENT
cd ..
HOME=$(cd $(dirname $0);pwd)
echo $HOME
cd ./pex/

# general setup

# export cell name
export CELL_NAME=hyscomp
export CELL_NAME=diff2sin
# export gds file path
export GDS_FILE=$HOME/gds/$CELL_NAME.gds
export SPICE_FILE=$HOME/netlist/$CELL_NAME.spice
export LVS_FILE=$HOME/lvs/$CELL_NAME.spice
export PEX_FILE=$HOME/pex/$CELL_NAME.spice

echo GDS
echo $GDS_FILE
echo SPICE
echo $SPICE_FILE
echo LVS
echo $LVS_FILE
echo PEX
echo $PEX_FILE
echo


## change
# export SPICE_FILE=$PEX_HOME/netlist/$CELL_NAME.spice
# export LVS_FILE=$PEX_HOME/netlist/lvs/$CELL_NAME.spice
# export PEX_FILE=$PEX_HOME/netlist/pex/$CELL_NAME.spice

## run DRC on a "good" GDS: expect no errors
echo "!!Running extraction for DRC!!"
magic -noconsole -dnull run_drc.tcl | tee drc.log
if grep -q "error tiles" drc.log ; then
    echo "Found DRC errors, which was not expected :-("
    exit 1
else
    echo "Found no DRC errors, as expected :-)"
fi


# comparator
# run LVS on a "good" GDS: expect no errors
echo "!!Running extraction for LVS and PEX!!"
magic -noconsole -dnull run_ext.tcl
netgen -batch lvs "$LVS_FILE $CELL_NAME" "$SPICE_FILE $CELL_NAME" $PDKPATH/libs.tech/netgen/sky130A_setup.tcl | tee lvs.log
if grep -q "Netlists do not match" lvs.log ; then
    echo "Found LVS errors, which was not expected :-("
    exit 1
else
    echo "Found no LVS errors, as expected :-)"
fi

exit 1

# python3 rewrite.py $PEX_FILE

# run SPICE simulation
# echo "Running SPICE simulation"
# echo "* Inverter simulation" > pre.spice
# echo ".lib \"$SKYWATER/libraries/sky130_fd_pr/latest/models/sky130.lib.spice\" tt" >> pre.spice
# cat pre.spice pex.spice post.spice > sim.spice
# ngspice -b sim.spice
