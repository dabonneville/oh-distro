#include <iostream>
#include <lcm/lcm-cpp.hpp>
#include "lcmtypes/drc_lcmtypes.hpp"
#include "RobotStateListener.hpp"

using namespace std;
using namespace boost;
using namespace visualization_utils;
using namespace collision;

namespace renderer_robot_state 
{
  //==================constructor / destructor
  
  /**Subscribes to Robot URDF Model and to EST_ROBOT_STATE.*/
  RobotStateListener::RobotStateListener(boost::shared_ptr<lcm::LCM> &lcm, BotViewer *viewer):
    _urdf_parsed(false),
    _lcm(lcm),
    _viewer(viewer)
  {
   _last_state_msg_timestamp = 0;
   _collision_detector = shared_ptr<Collision_Detector>(new Collision_Detector());
    //lcm ok?
    if(!lcm->good())
    {
      cerr << "\nLCM Not Good: Robot State Handler" << endl;
      return;
    }

    // Subscribe to Robot_Model.  Will unsubscribe once a single message has been received
    _urdf_subscription = lcm->subscribe("ROBOT_MODEL", 
				       &RobotStateListener::handleRobotUrdfMsg,
				       this);    
    _urdf_subscription_on = true;
    //Subscribes to MEAS_JOINT_ANGLES 
    //lcm->subscribe("MEAS_JOINT_ANGLES", &RobotStateListener::handleJointAnglesMsg, this); 
    lcm->subscribe("EST_ROBOT_STATE", &RobotStateListener::handleRobotStateMsg, this); 
 
  }

  RobotStateListener::~RobotStateListener() {
     _collision_detector->clear_collision_objects(); 
  }

//-------------------------------------------------------------------------------------      
//=============message callbacks

  //void RobotStateListener::handleJointAnglesMsg(const lcm::ReceiveBuffer* rbuf,
  //						 const string& chan, 
  //						 const drc::joint_angles_t* msg)
  void RobotStateListener::handleRobotStateMsg(const lcm::ReceiveBuffer* rbuf,
						 const string& chan, 
						 const drc::robot_state_t* msg)						 
  {
    
    //int64_t tic = bot_timestamp_now();
    if (!_urdf_parsed)
    {
     //cout << msg->utime << endl;
      //cout << "\n handleRobotStateMsg: Waiting for urdf to be parsed" << endl;
      return;
    }
    if(_urdf_subscription_on)
    {			
      cout << "\n handleRobotStateMsg: unsubscribing from _urdf_subscription" << endl;
      _lcm->unsubscribe(_urdf_subscription);     //unsubscribe from urdf messages
      _urdf_subscription_on =  false; 	
    }
    
    // Render at 100Hz of Real Time. Too much rendering will make the viewer less reponsive.
    //cout << msg->utime - _last_state_msg_timestamp << endl;
		int64_t now = bot_timestamp_now();//msg->utime
    if(now-_last_state_msg_timestamp >= 10000)  // timestamps are in usec
    {
    // cout << now - _last_state_msg_timestamp << endl;
    _gl_robot->set_state(*msg);
    bot_viewer_request_redraw(_viewer);
     _last_state_msg_timestamp = now;//msg->utime;
    }

    //int64_t toc = bot_timestamp_now();
    //cout << bot_timestamp_useconds(toc-tic) << endl;
    
  } // end handleMessage

//-------------------------------------------------------------------------------------        
  void RobotStateListener::handleRobotUrdfMsg(const lcm::ReceiveBuffer* rbuf, const string& channel, 
					       const  drc::robot_urdf_t* msg) 
  {

    if(_urdf_parsed ==false) 
    {
      cout<< "\nurdf handler @ RobotStateListener" << endl;
      // Received robot urdf string. Store it internally and get all available joints.
      _robot_name      = msg->robot_name;
      _urdf_xml_string = msg->urdf_xml_string;
      cout<< "\nReceived urdf_xml_string of robot [" 
      << msg->robot_name << "], storing it internally as a param" << endl;

      bot_gtk_gl_drawing_area_set_context(this->_viewer->gl_area); // Prevents conflict with cam renderer which messes with the gl context
      _gl_robot = shared_ptr<visualization_utils::InteractableGlKinematicBody>(new visualization_utils::InteractableGlKinematicBody(_urdf_xml_string,_collision_detector,true,_robot_name));
  
      cout<< "Number of Joints: " << _gl_robot->get_num_joints() <<endl;
      
      //remember that we've parsed the urdf already
      _urdf_parsed = true;
    }
 
  } // end urdf handler



} //namespace renderer_robot_state


