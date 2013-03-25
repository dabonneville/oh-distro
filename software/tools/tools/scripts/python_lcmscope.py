#!/usr/bin/python

import os,sys
import lcm
import time
from lcm import LCM
import math
import numpy  as np
import matplotlib.pyplot as plt
import matplotlib.mlab as mlab

from threading import Thread

home_dir =os.getenv("HOME")
#print home_dir
sys.path.append(home_dir + "/drc/software/build/lib/python2.7/site-packages")
sys.path.append(home_dir + "/drc/software/build/lib/python2.7/dist-packages")
from bot_core.pose_t import pose_t
from bot_core.planar_lidar_t import planar_lidar_t
#from mav.filter_state_t import filter_state_t
from microstrain.ins_t import ins_t
from fovis.update_t import update_t

from drc.robot_state_t import robot_state_t
from drc.imu_t import imu_t #... not to be confused with ins_t
from drc.utime_t import utime_t #... not to be confused with ins_t
########################################################################################

def timestamp_now (): return int (time.time () * 1000000)

class SensorData(object):
    def __init__(self, nfields):
        self.nfields = nfields
        self.reset()
    def append(self, utime,v_in ):
        np_v = np.array(v_in)
        # reset if shape is different
        if (self.v.shape[1] != np_v.size):
          self.nfields = np_v.size
          self.reset()
        np_utimes = np.array( (utime - first_utime)/1000000.0 )
        self.utimes = np.vstack((self.utimes , np_utimes ))
        self.v = np.vstack((self.v , np_v ))
    def reset(self):
        # no sure how to support initialising a Nx0 array, so I'm initing a Nx1 array and skipping 1st row:
        self.utimes=np.array([0]) 
        self.v=np.zeros((1, self.nfields))


def reset_all():
  pos.reset(); posrate.reset()
  ang.reset(); angrate.reset(); 
  ins_angrate.reset(); ins_posaccel.reset();
  vo_posdelta.reset(); vo_posrate.reset(); 
  vo_angdelta.reset(); vo_angrate.reset();
  lf_force.reset(); lf_torque.reset();
  rf_force.reset(); rf_torque.reset();
  


def quat_to_euler(q) :
  roll = math.atan2(2*(q[0]*q[1]+q[2]*q[3]), 1-2*(q[1]*q[1]+q[2]*q[2]));
  pitch = math.asin(2*(q[0]*q[2]-q[3]*q[1]));
  yaw = math.atan2(2*(q[0]*q[3]+q[1]*q[2]), 1-2*(q[2]*q[2]+q[3]*q[3]));
  return [roll,pitch,yaw]

def plot_data():
  global last_utime
  front_block =0 # offset into the future (to ensure no recent data not viewed)
  if ( len(pos.utimes) >1):
    plt.figure(1)
    ############################################################
    ax1.cla()
    ax1.plot(pos.utimes[1:], np.transpose(pos.v[1:,0]), 'r', linewidth=1,label="x")
    ax1.plot(pos.utimes[1:], np.transpose(pos.v[1:,1]), 'g', linewidth=1,label="y")
    ax1.plot(pos.utimes[1:], np.transpose(pos.v[1:,2]), 'b', linewidth=1,label="z")
    ax1.legend();  ax1.set_xlabel('Time '+ str(last_utime));  ax1.set_ylabel('Local Pos [m]');  ax1.grid(True)
    ax1.legend(loc=2,prop={'size':10})
    ax1.set_xlim( (last_utime - plot_window - first_utime)/1000000 , (last_utime + front_block - first_utime)/1000000 )
    ############################################################
    ax2.cla()
    ax2.plot(ins_posaccel.utimes[1:], np.transpose(ins_posaccel.v[1:,0]), 'r', linewidth=1,label="x accel")
    ax2.plot(ins_posaccel.utimes[1:], np.transpose(ins_posaccel.v[1:,1]), 'g', linewidth=1,label="y accel")
    ax2.plot(ins_posaccel.utimes[1:], np.transpose(ins_posaccel.v[1:,2]), 'b', linewidth=1,label="z accel")
    ax2.legend();  ax2.set_xlabel('Time '+ str(last_utime));  ax2.set_ylabel('Acceloration [m/s2]');  ax2.grid(True)
    ax2.legend(loc=2,prop={'size':10})
    ax2.set_xlim( (last_utime - plot_window - first_utime)/1000000 , (last_utime + front_block - first_utime)/1000000 )
    ###################### TODO - add this back in and remove the element above and put in a different window
    #ax2.cla()
    #ax2.plot(posrate.utimes[1:], np.transpose(posrate.v[1:,0]), 'r', linewidth=1,label="u fwd")
    #ax2.plot(posrate.utimes[1:], np.transpose(posrate.v[1:,1]), 'g', linewidth=1,label="v left")
    #ax2.plot(posrate.utimes[1:], np.transpose(posrate.v[1:,2]), 'b', linewidth=1,label="w up")
    # also add VO posrates: [linear velocity]
    #ax2.plot(vo_posrate.utimes[1:],  np.transpose(vo_posrate.v[1:,0]), 'r+', linewidth=1,label="VO u fwd")
    #ax2.plot(vo_posrate.utimes[1:],  np.transpose(vo_posrate.v[1:,1]), 'g+', linewidth=1,label="VO v left")
    #ax2.plot(vo_posrate.utimes[1:],  np.transpose(vo_posrate.v[1:,2]), 'b+', linewidth=1,label="VO w up")
    #ax2.legend();   ax2.set_xlabel('Time - vo: ' + str(len(vo_posrate.utimes)));   ax2.set_ylabel('Body Pos Rate [m/s]');   ax2.grid(True)
    #ax2.legend(loc=2,prop={'size':10})
    #ax2.set_xlim( (last_utime - plot_window - first_utime)/1000000 , (last_utime + front_block - first_utime)/1000000 )
    ##ax2.set_ylim(-2,2)
    ############################################################
    ax3.cla()
    ax3.plot(ang.utimes[1:], np.transpose(ang.v[1:,0]) *180/math.pi , 'r', linewidth=1,label="roll")
    ax3.plot(ang.utimes[1:], np.transpose(ang.v[1:,1]) *180/math.pi , 'm', linewidth=1,label="pitch")
    ax3.plot(ang.utimes[1:], np.transpose(ang.v[1:,2]) *180/math.pi , 'y', linewidth=1,label="yaw")
    ax3.legend();   ax3.set_xlabel('Time - pose: ' + str(len(ang.utimes)));   ax3.set_ylabel('Local Angle [Deg]');   ax3.grid(True)
    ax3.legend(loc=2,prop={'size':10})
    ax3.set_xlim( (last_utime - plot_window - first_utime)/1000000 , (last_utime + front_block - first_utime)/1000000 )
    ############################################################
    ax4.cla()
    ax4.plot(angrate.utimes[1:], np.transpose(angrate.v[1:,0]), 'r', linewidth=1,label="p")
    ax4.plot(angrate.utimes[1:], np.transpose(angrate.v[1:,1]), 'm', linewidth=1,label="q")
    ax4.plot(angrate.utimes[1:], np.transpose(angrate.v[1:,2]), 'y', linewidth=1,label="r")
    #print len(ins_angrate.utimes[1:])
    #print len(np.transpose(ins_angrate.v[1:,0]))
    ax4.plot(ins_angrate.utimes[1:], -1* np.transpose(ins_angrate.v[1:,0]), 'r:', linewidth=1,label="-g0")
    ax4.plot(ins_angrate.utimes[1:],     np.transpose(ins_angrate.v[1:,1]), 'm:', linewidth=1,label="g1")
    ax4.plot(ins_angrate.utimes[1:], -1* np.transpose(ins_angrate.v[1:,2]), 'y:', linewidth=1,label="-g2")
    # also add VO angrates:
    ax4.plot(vo_angrate.utimes[1:],  np.transpose(vo_angrate.v[1:,0]), 'r+', linewidth=1,label="VO roll rate")
    ax4.plot(vo_angrate.utimes[1:],  np.transpose(vo_angrate.v[1:,1]), 'm+', linewidth=1,label="VO pitch rate")
    ax4.plot(vo_angrate.utimes[1:],  np.transpose(vo_angrate.v[1:,2]), 'y+', linewidth=1,label="VO yaw rate")
    # Gazebo Measurements:
    ax4.legend();   ax4.set_xlabel('Time - ins: ' + str(len(ins_angrate.utimes)));  ax4.set_ylabel('Body Angle Rate [Deg/s]');   ax4.grid(True)
    ax4.legend(loc=2,prop={'size':10})
    ax4.set_xlim( (last_utime - plot_window - first_utime)/1000000 , (last_utime + front_block - first_utime)/1000000 )


  if (len(lf_force.utimes) >1):
    # VO time (skip 2nd one also as its always zero:)
    plt.figure(2)
    ax5.cla()
    ax5.plot(lf_force.utimes[2:],     np.transpose(lf_force.v[2:,0]), 'b',  linewidth=1,label="Left")
    #ax5.plot(lf_force.utimes[1:],     np.transpose(lf_force.v[1:,1]), 'b+', linewidth=1,label="Left Y")
    #ax5.plot(lf_force.utimes[1:],     np.transpose(lf_force.v[1:,2]), 'b:', linewidth=1,label="Left Z")
    ax5.plot(rf_force.utimes[2:],     np.transpose(rf_force.v[2:,0]), 'r',  linewidth=1,label="Right")
    #ax5.plot(rf_force.utimes[1:],     np.transpose(rf_force.v[1:,1]), 'r+', linewidth=1,label="Right Y")
    #ax5.plot(rf_force.utimes[1:],     np.transpose(rf_force.v[1:,2]), 'r.', linewidth=1,label="Right Z")
    ax5.legend(loc=2,prop={'size':10});   ax5.set_xlabel('Time '+ str(last_utime));   ax5.set_ylabel('Force [?? units]');   ax5.grid(True)
    ax5.set_xlim( (last_utime - plot_window - first_utime)/1000000 , (last_utime + front_block- first_utime)/1000000 )
    ax5.set_ylim( -1200, 100 )
    # Vo angle rates:
    ax6.cla()
    ax6.plot(lf_torque.utimes[2:],     np.transpose(lf_torque.v[2:,0]), 'b',  linewidth=1,label="Left X")
    ax6.plot(lf_torque.utimes[2:],     np.transpose(lf_torque.v[2:,1]), 'b+', linewidth=1,label="Left Y")
    ax6.plot(lf_torque.utimes[2:],     np.transpose(lf_torque.v[2:,2]), 'b:', linewidth=1,label="Left Z")
    ax6.plot(rf_torque.utimes[2:],     np.transpose(rf_torque.v[2:,0]), 'r',  linewidth=1,label="Right X")
    ax6.plot(rf_torque.utimes[2:],     np.transpose(rf_torque.v[2:,1]), 'r+', linewidth=1,label="Right Y")
    ax6.plot(rf_torque.utimes[2:],     np.transpose(rf_torque.v[2:,2]), 'r.', linewidth=1,label="Right Z")
    ax6.legend(loc=2,prop={'size':10});   ax6.set_xlabel('Time '+ str(last_utime));   ax6.set_ylabel('Torque [?? units]');   ax5.grid(True)
    ax6.set_xlim( (last_utime - plot_window - first_utime)/1000000 , (last_utime + front_block - first_utime)/1000000 )
    ax6.set_ylim( -1200, 100 )
    # VO angle delta - measured change in angle:
    ax7.cla()
    ax7.plot(vo_angdelta.utimes[1:],  np.transpose(vo_angdelta.v[1:,0]), 'r+', linewidth=1,label="roll")
    ax7.plot(vo_angdelta.utimes[1:],  np.transpose(vo_angdelta.v[1:,1]), 'm+', linewidth=1,label="pitch")
    ax7.plot(vo_angdelta.utimes[1:],  np.transpose(vo_angdelta.v[1:,2]), 'y+', linewidth=1,label="yaw")
    ax7.legend();   ax7.set_xlabel('Time');   ax7.set_ylabel('VO Body Angle Delta [Deg]');   ax7.grid(True)
    ax7.legend(loc=2,prop={'size':10})
    ax7.set_xlim( (last_utime - plot_window - first_utime)/1000000 , (last_utime + front_block - first_utime)/1000000 )
    # vo_posdelta - measured change in position:
    ax8.cla()
    ax8.plot(vo_posdelta.utimes[1:],  np.transpose(vo_posdelta.v[1:,0]), 'r+', linewidth=1,label="dx fwd")
    ax8.plot(vo_posdelta.utimes[1:],  np.transpose(vo_posdelta.v[1:,1]), 'g+', linewidth=1,label="dy left")
    ax8.plot(vo_posdelta.utimes[1:],  np.transpose(vo_posdelta.v[1:,2]), 'b+', linewidth=1,label="dz up")
    ax8.legend();   ax8.set_xlabel('Time');   ax8.set_ylabel('VO Body Delta Pos [m]');   ax8.grid(True)
    ax8.legend(loc=2,prop={'size':10})
    ax8.set_xlim( (last_utime - plot_window - first_utime)/1000000 , (last_utime + front_block - first_utime)/1000000 )
    
  if (len(utime_10hz_rate.utimes) >1):
    plt.figure(3)
    ax9.cla()
    ax9.plot(utime_10hz_rate.utimes[2:],     np.transpose(utime_10hz_rate.v[2:,0]), 'b',  linewidth=1,label="10Hz samples")
    ax9.plot(utime_1hz_rate.utimes[2:],     np.transpose(utime_1hz_rate.v[2:,0]), 'r',  linewidth=1,label="1Hz samples")
    ax9.legend(loc=2,prop={'size':10});   ax9.set_xlabel('Time '+ str(last_utime));   ax9.set_ylabel('Fraction Realtime');   ax9.grid(True)
    ax9.set_ylim(0, 1);
    ax9.set_xlim( (last_utime - plot_window - first_utime)/1000000 , (last_utime + front_block- first_utime)/1000000 )
    
  plt.plot()
  plt.draw()
  

def on_relvo(channel, data):
  m = update_t.decode(data)
  #print "K T:      %.3f" % (m.timestamp)
  #print "KPT:      %.3f" % (m.prev_timestamp)
  pyr=quat_to_euler(m.rotation)
  vo_delta_time = (m.timestamp - m.prev_timestamp)/1000000.0
  #convert camera pyr to body rpy #########################
  #TODO: use rotation matrix
  rpyt = [pyr[2], -pyr[0], -pyr[1], vo_delta_time]
  vo_angdelta.append(m.timestamp,rpyt)
  rpy_rate_t = [pyr[2]/vo_delta_time, -pyr[0]/vo_delta_time, -pyr[1]/vo_delta_time, vo_delta_time]
  vo_angrate.append(m.timestamp,rpy_rate_t)
  #covert camera translation into body translation ########
  posdelta_t = [m.translation[2], -m.translation[0], -m.translation[1], vo_delta_time]
  vo_posdelta.append(m.timestamp,posdelta_t)
  posrate_t = [m.translation[2]/vo_delta_time, -m.translation[0]/vo_delta_time, -m.translation[1]/vo_delta_time, vo_delta_time]
  vo_posrate.append(m.timestamp,posrate_t)
  #global last_utime
  #if (m.timestamp < last_utime):
  #  print "out of order data, resetting now %s | last %s"   %(m.timestamp,last_utime)
  #  reset_all()
  #last_utime = m.timestamp

# Microstrain INS/IMU Sensor:
def on_ins(channel, data):
  m = ins_t.decode(data)
  ins_angrate.append(m.utime,m.gyro)
  ins_posaccel.append(m.utime,m.accel)
  #print "IMU:      %.3f" % (m.utime)

def on_pose(channel, data):
  m = pose_t.decode(data)
  global first_utime
  if (first_utime==0):
    first_utime= m.utime
  pos.append(m.utime,  [m.pos[0], m.pos[1], m.pos[2]] )
  ang.append(m.utime,quat_to_euler(m.orientation))
  #print "p %s" % (p.utime)
  dt = float(  timestamp_now() - m.utime )/1000000
  global last_utime
  if (m.utime < last_utime):
    print "out of order data, resetting now %s | last %s"   %(m.utime,last_utime)
    reset_all()
  last_utime = m.utime
  #plot_data()
  #print "POSE:      %.3f" % (dt)

def on_state(channel, data):
  m = filter_state_t.decode(data)
  angrate.append(m.utime,  [m.state[0], m.state[1], m.state[2]] )
  posrate.append(m.utime,  [m.state[3], m.state[4], m.state[5]] )
  pos.append(m.utime,  [m.state[9], m.state[10], m.state[11]] )
  ang.append(m.utime,quat_to_euler(m.quat))
  global last_utime
  if (m.utime < last_utime):
    print "out of order data, resetting now %s | last %s"   %(m.utime,last_utime)
    reset_all()
  last_utime = m.utime
  #print "STATE     %.3f" % (m.utime)



################################## DRC SPECIFIC #####################################################
def on_robot_state(channel, data):
  m = robot_state_t.decode(data)
  # assumes left foot, right foot
  lf_torque.append(m.utime,  [m.contacts.contact_torque[0].x, m.contacts.contact_torque[0].y , m.contacts.contact_torque[0].z  ] )
  rf_torque.append(m.utime,  [m.contacts.contact_torque[1].x, m.contacts.contact_torque[1].y , m.contacts.contact_torque[1].z  ] )
  # ignore x,y, they are zero
  lf_force.append(m.utime,  [m.contacts.contact_force[0].z])#, m.contacts.contact_force[0].y , m.contacts.contact_force[0].z  ] )
  rf_force.append(m.utime,  [m.contacts.contact_force[1].z])#, m.contacts.contact_force[1].y , m.contacts.contact_force[1].z  ] )
  #print "EST_R_STATE     %.3f" % (m.utime)

# Gazebo Simulated IMU:
def on_imu(channel, data):
  m = imu_t.decode(data)
  ins_angrate.append(m.utime,m.angular_velocity)
  ins_posaccel.append(m.utime,m.linear_acceleration)
  #print "ins"
  #print len(ins_angrate.utimes[1:])
  #print len(np.transpose(ins_angrate.v[1:,0]))
  #print "Gazebo IMU:      %.3f" % (m.utime)


  
last_10hz_rbot_time =0
last_10hz_wall_time = timestamp_now ()
last_1hz_rbot_time =0
last_1hz_wall_time = timestamp_now ()
bot_utime_list=[]
def on_utime(channel, data):  
  global last_10hz_rbot_time, last_10hz_wall_time, last_1hz_rbot_time, last_1hz_wall_time
  m = utime_t.decode(data)
  curr_wall_time = timestamp_now ()
  if (m.utime > last_1hz_rbot_time + 1000000):
    frac = float( m.utime - last_1hz_rbot_time ) / float(curr_wall_time  - last_1hz_wall_time)
    utime_1hz_rate.append(m.utime,frac)
    last_1hz_wall_time = curr_wall_time
    last_1hz_rbot_time = m.utime
  if (m.utime > last_10hz_rbot_time + 100000):
    #print "================="
    #print m.utime
    #print last_10hz_rbot_time
    #print float(m.utime - last_10hz_rbot_time)
    #print float(curr_wall_time  - last_10hz_rbot_time)
    frac = float( m.utime - last_10hz_rbot_time ) / float(curr_wall_time  - last_10hz_wall_time)
    #print frac
    utime_10hz_rate.append(m.utime,frac)
    last_10hz_wall_time = curr_wall_time
    last_10hz_rbot_time = m.utime
  
#################################################################################

lc = lcm.LCM()
print "started"
last_utime=0
first_utime=0
plot_window=3*1000000 #3sec
pos = SensorData(3); posrate = SensorData(3); 
ang = SensorData(3); angrate = SensorData(3); 
ins_angrate = SensorData(3); ins_posaccel = SensorData(3); # raw ins angrates and linear accelorations
vo_posdelta = SensorData(4); vo_posrate = SensorData(4); 
vo_angdelta = SensorData(4); vo_angrate = SensorData(4);

lf_force = SensorData(1); rf_force = SensorData(1); # left and right foot. z only ignore x&y
lf_torque = SensorData(3); rf_torque = SensorData(3); # left and right foot

utime_10hz_rate = SensorData(1); utime_1hz_rate = SensorData(1); 

left, bottom, width, height =0.07, 0.07, 0.395, 0.395
box_ul = [left, 2*bottom+height, width, height]
box_ur = [2*left+width, 2*bottom+height, width, height]
box_ll = [left, bottom, width, height]
box_lr = [2*left+width, bottom, width, height]

fig2 = plt.figure(num=2, figsize=(14, 10), dpi=80, facecolor='w', edgecolor='k')
ax5 = fig2.add_axes(box_ul)
ax6 = fig2.add_axes(box_ur)
ax7 = fig2.add_axes(box_ll)
ax8 = fig2.add_axes(box_lr)

fig3 = plt.figure(num=3, figsize=(14, 10), dpi=80, facecolor='w', edgecolor='k')
ax9 = fig3.add_axes(box_ul)
ax10 = fig3.add_axes(box_ur)
ax11 = fig3.add_axes(box_ll)
ax12 = fig3.add_axes(box_lr)

plt.interactive(True)
plt.plot()
plt.draw()

fig1 = plt.figure(num=1, figsize=(14, 10), dpi=80, facecolor='w', edgecolor='k')
ax1 = fig1.add_axes(box_ul)
ax2 = fig1.add_axes(box_ur)
ax3 = fig1.add_axes(box_ll)
ax4 = fig1.add_axes(box_lr)

def lcm_thread():
  sub1 = lc.subscribe("POSE_HEAD", on_pose) # required
  ##sub2 = lc.subscribe("STATE_ESTIMATOR_STATE", on_state)
  #sub3 = lc.subscribe("MICROSTRAIN_INS", on_ins)
  #sub4 = lc.subscribe("KINECT_REL_ODOMETRY", on_relvo)

  # DRC msgs
  sub5 = lc.subscribe("EST_ROBOT_STATE", on_robot_state)
  #sub6 = lc.subscribe("HEAD_IMU", on_imu)
  sub7 = lc.subscribe("ROBOT_UTIME", on_utime)

  
  while True:
    ## Handle LCM if new messages have arrived.
    lc.handle()

  lc.unsubscribe(sub1)
  lc.unsubscribe(sub2)
  lc.unsubscribe(sub3)
  lc.unsubscribe(sub4)
  lc.unsubscribe(sub5)
  lc.unsubscribe(sub6)
  lc.unsubscribe(sub7)

t2 = Thread(target=lcm_thread)
t2.start()

time.sleep(3) # wait for some data- could easily remove

plot_timing=0.1 # time between updates of the plots - in wall time
while (1==1):
  time.sleep(plot_timing)
  tic_ms = float(round(time.time() * 1000))
  plot_data()
  toc_ms = float(round(time.time() * 1000))
  dt_sec = (toc_ms - tic_ms)/1000
  print "drawing time: %f" %(dt_sec)




