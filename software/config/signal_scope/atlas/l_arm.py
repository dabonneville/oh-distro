import numpy
import colorsys

# joints to plot
joints = ["rightHipYaw", "rightHipRoll", "rightHipPitch", "rightKneePitch", "rightAnklePitch", "rightAnkleRoll"]

left_arm_joints = ['l_arm_shz','l_arm_shx','l_arm_ely','l_arm_elx','l_arm_uwy',
  'l_arm_mwx', 'l_arm_lwy']


joints = left_arm_joints

joints = ['l_arm_shx']
# string arrays for EST_ROBOT_STATE and ATLAS_COMMAND
jn = msg.joint_name
jns = msg.joint_names

N = len(joints)
HSV_tuples =      [(0., 1.0, 1.0),(0.15, 1.0, 1.0), (0.3, 1.0, 1.0), (0.45, 1.0, 1.0), (0.6, 1.0, 1.0), (0.75, 1.0, 1.0), (0.9, 1.0, 1.0)]
HSV_tuples_dark = [(0., 1.0, 0.5),(0.15, 1.0, 0.5), (0.3, 1.0, 0.5), (0.45, 1.0, 0.5), (0.6, 1.0, 0.5), (0.75, 1.0, 0.5), (0.9, 1.0, 0.5)]
HSV_tuples_v3 = [(0.,0.75, 0.5),(0.15,0.75, 0.5), (0.3,0.75, 0.5), (0.45,0.75, 0.5), (0.6,0.75, 0.5), (0.75,0.75, 0.5), (0.9,0.75, 0.5)]

HSV_tuples =      [(0.15, 1.0, 1.0), (0.3, 1.0, 1.0), (0.45, 1.0, 1.0), (0.6, 1.0, 1.0), (0.75, 1.0, 1.0), (0.9, 1.0, 1.0)]
HSV_tuples_dark = [(0., 1.0, 0.5),(0.15, 1.0, 0.5), (0.3, 1.0, 0.5), (0.45, 1.0, 0.5), (0.6, 1.0, 0.5), (0.75, 1.0, 0.5), (0.9, 1.0, 0.5)]
HSV_tuples_v3 = [(0.3,0.75, 0.5), (0.45,0.75, 0.5), (0.6,0.75, 0.5), (0.75,0.75, 0.5), (0.9,0.75, 0.5)]

RGB_tuples = map(lambda x: colorsys.hsv_to_rgb(*x), HSV_tuples)
RGB_tuples_dark = map(lambda x: colorsys.hsv_to_rgb(*x), HSV_tuples_dark)
RGB_tuples_v3 = map(lambda x: colorsys.hsv_to_rgb(*x), HSV_tuples_v3)

# position plot
addPlot(timeWindow=15, yLimits=[-1.5, 1.5])
addSignals('ATLAS_COMMAND', msg.utime, msg.position, joints, keyLookup=jns, colors=RGB_tuples)
addSignals('EST_ROBOT_STATE', msg.utime, msg.joint_position, joints, keyLookup=jn, colors=RGB_tuples_v3)

addSignals('CONTROLLER_STATE', msg.timestamp, msg.q_des, joints, keyLookup=jn,colors=RGB_tuples_dark)

addSignal('QP_CONTROLLER_INPUT', msg.timestamp, msg.whole_body_data.q_des[16])
