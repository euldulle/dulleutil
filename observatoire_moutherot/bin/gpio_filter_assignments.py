import os
import urllib
import urllib.request
#
#  TS stepper focuser
#
o_step_ts=17
o_dir_ts=27
o_enable_ts=22
#
#  C14 stepper focuser
#
o_step_c14=16   # odroid IO (used by the eul_focuser indi driver): 33 
o_dir_c14=13    # odroid IO (used by the eul_focuser indi driver): 31 
o_enable_c14=22 # odroid IO (used by the eul_focuser indi driver): 22 
#
#  DC command
#
O_focus_in=7
O_focus_out=12
#
# pad input buttons :
#
I_focus_in=16
I_focus_out=20
#
#
#
# filterwheel sensor
#
o_sensor_fw=23
#
#
# filterwheel stepper control :
o_step_fw=4
o_dir_fw=5
o_enable_fw=25
# filterwheel filter assignments
olm_fw_filters=[" UNKNOWN ", "LUMINANCE", "   RED    ", "  GREEN   ", "  BLUE  ", "   Ha    "]

olm_fw_fifoname="/home/fmeyer/filter_wheel_fifo"
olm_fw_statefile="/home/fmeyer/filter_wheel_state"

fw_drv_addr=0
c14_drv_addr=1
ts_drv_addr=2
OFF=0
ON=1
basew16=os.environ["OLM_BASER16"]

def pwr_stepper(driver_addr,onoff):
    url="%s/%.2d"%(basew16,2*driver_addr+onoff)
    urllib.request.urlretrieve(url)

