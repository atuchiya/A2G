# http://opencircuitdesign.com/magic/

# read design
gds read $::env(GDS_FILE)
load $::env(CELL_NAME)

echo 
echo DRC START
# count number of DRC errors
drc euclidean on
drc catchup
drc check
drc count
drc find
drc why
echo DRC FINISH!!

# quit
quit
