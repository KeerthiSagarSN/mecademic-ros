#! /usr/bin/env python3
import rospy
from geometry_msgs.msg import Pose, TwistStamped
from sensor_msgs.msg import JointState
from std_msgs.msg import String, Bool, UInt8MultiArray
import time

# For these imports to work in ROS, the PYTHONPATH needs to be updated with 
# the working directory of this script, with the MecademicRobot package in the 
# same location and the RobotController.py and RobotFeedback.py in that package 
# folder

#---------------------------------------#
# type this into the linux command line before running the launch file  
# $ export PYTHONPATH="${PYTHONPATH}:/path/to/your/project/"
#---------------------------------------#

from MecademicRobot.RobotController import *
from MecademicRobot.RobotFeedback import *

class MecademicRobot_Driver():
    """ROS Mecademic Robot Node Class to make a Node for the Mecademic Robot

    Attributes:
        subscriber: ROS subscriber to send command to the Mecademic Robot through a topic
        publisher: ROS publisher to place replies from the Mecademic Robot in a topic 
        MecademicRobot : driver to control the MecademicRobot Robot
    """
    def __init__(self, robot, feedback):
        """Constructor for the ROS MecademicRobot Driver
        """
        rospy.init_node("MecademicRobot_driver", anonymous=True)
        self.joint_subscriber  = rospy.Subscriber("MecademicRobot_joint", JointState, self.joint_callback)
        self.pose_subscriber   = rospy.Subscriber("MecademicRobot_pose", Pose, self.pose_callback)
        self.velocity_subscriber   = rospy.Subscriber("MecademicRobot_vel", TwistStamped, self.twist_callback, queue_size=1)
        self.command_subcriber = rospy.Subscriber("MecademicRobot_command", String, self.command_callback)
        self.gripper_subcriber = rospy.Subscriber("MecademicRobot_gripper", Bool, self.gripper_callback)
        #Keerthi code here
        #self.setTRF_subscriber = rospy.Subscriber("MecademicRobot_setTRF", Pose, self.setTRF_callback)
        self.reply_publisher   = rospy.Publisher("MecademicRobot_reply", String, queue_size=1)
        self.joint_publisher   = rospy.Publisher("MecademicRobot_joint_fb", JointState, queue_size=1) 
        self.pose_publisher    = rospy.Publisher("MecademicRobot_pose_fb", Pose, queue_size=1)
        self.status_publisher  = rospy.Publisher("MecademicRobot_status", UInt8MultiArray, queue_size=1)
        
        
        self.robot = robot
        self.feedback = feedback

        self.socket_available = True

        self.feedbackLoop()

    def command_callback(self, command):
        """Forwards a ascii command to the Mecademic Robot

        :param command: ascii command to forward to the Robot
        """
        while(not self.socket_available):       #wait for socket to be available
            pass
        self.socket_available = False              #block socket from being used in other processes
        if(self.robot.is_in_error()):
            self.robot.ResetError()
            self.robot.ResumeMotion()
        reply = self.robot.exchangeMsg(command.data, decode=False)
        self.socket_available = True               #Release socket so other processes can use it
        if(reply is not None):
            self.reply_publisher.publish(reply)
        
    def joint_callback(self, joints):
        """Callback when the MecademicRobot_emit topic receives a message
        Forwards message to driver that translate into real command
        to the Mecademic Robot

        :param joints: message received from topic containing position and velocity information
        """
        

        
        while(not self.socket_available):               #wait for the socket to be available
            pass
        reply = None
        self.socket_available = False                      #Block other processes from using the socket
        if(self.robot.is_in_error()):
            self.robot.ResetError()
            self.robot.ResumeMotion()
            print('Errro scenario')
        if(len(joints.velocity)>0):
            self.robot.SetJointVel(joints.velocity[0])
        if(len(joints.position)==6):
            joints.position = [i*180/3.14159 for i in joints.position]# - Changing from default - Degrees to radians - Seems stupid to do double conversion
            #print('Moving all joints')
            #joints.position = [i for i in joints.position] # Absolute angle in Radians rather than degrees - As KDL outputs [rad]
            
            reply = self.robot.MoveJoints(joints.position[0],joints.position[1],joints.position[2],joints.position[3],joints.position[4],joints.position[5])
            
            
            #print('controller - Joints',joints.position)
        '''
        elif(len(joints.position)==4):
            reply = self.robot.MoveJoints(joints.position[0],joints.position[1],joints.position[2],joints.position[3])
        '''
        self.socket_available = True                       #Release the socket so other processes can use it
        
        
        if(reply is not None):
            self.reply_publisher.publish(reply)
        
    def pose_callback(self, pose):
        """Callback when the MecademicRobot_emit topic receives a message
        Forwards message to driver that translate into real command
        to the Mecademic Robot

        :param pose: message received from topic containing position and orientation information
        """
        while(not self.socket_available):           #wait for socket to become available
            pass
        reply = None
        self.socket_available = False                  #Block other processes from using the socket while in use
        if(self.robot.is_in_error()):
            self.robot.ResetError()
            self.robot.ResumeMotion()
        if(pose.position.z is not None):
            reply = self.robot.MovePose(pose.position.x,pose.position.y,pose.position.z,pose.orientation.x,pose.orientation.y,pose.orientation.z)
        else:
            reply = self.robot.MovePose(pose.position.x,pose.position.y,pose.orientation.x,pose.orientation.y)
        self.socket_available = True                   #Release socket so other processes can continue
        if(reply is not None):
            self.reply_publisher.publish(reply)   
    
    
    ## Philip's code starts here
    def twist_callback(self, twist):
        """Callback when the MecademicRobot_emit topic receives a message
        Forwards message to driver that translate into real command
        to the Mecademic Robot

        :param pose: message received from topic containing position and orientation information
        """
        while(not self.socket_available):           #wait for socket to become available
            pass
        reply = None
        self.socket_available = False                  #Block other processes from using the socket while in use
        if(self.robot.is_in_error()):
            self.robot.ResetError()
            self.robot.ResumeMotion()
          
        if(twist.header.frame_id == 'base'):
            print("linear move")
            reply = self.robot.MoveLinVelWRF(twist.twist.linear.x,twist.twist.linear.y,twist.twist.linear.z,twist.twist.angular.x,twist.twist.angular.y,twist.twist.angular.z)        
            
            #print("I have cleared Motion")

        elif(twist.header.frame_id == 'tool'):
            print("angular move")
            reply = self.robot.MoveLinVelTRF(twist.twist.linear.x,twist.twist.linear.y,twist.twist.linear.z,twist.twist.angular.x,twist.twist.angular.y,twist.twist.angular.z)        
        else:
            print('Unrecognized Frame')

        self.socket_available = True                   #Release socket so other processes can continue
        if(reply is not None):
            self.reply_publisher.publish(reply)  
            
    def gripper_callback(self, state):
        """Controls whether to open or close the gripper.
        True for open, False for close

        :param state: ROS Bool message
        """
        while(not self.socket_available):       #wait for socket to be available
            pass
        self.socket_available = False              #Block other processes from using the socket
        if(self.robot.is_in_error()):
            self.robot.ResetError()
            self.robot.ResumeMotion()
        if(state.data):
            reply = self.robot.GripperOpen()
            print('KEERTHI PRINT GRIPPER CLOSE')
        else:
            reply = self.robot.GripperClose()
            print('KEERTHI PRINT GRIPPER CLOSE')
        self.socket_available = True               #Release socket so other processes can use it
        if(reply is not None):
            self.reply_publisher.publish(reply)             

    def feedbackLoop(self):
        """Retrieves live position feedback and publishes the data 
        to its corresponding topic. (infinite loop)
        """
        joints_fb = JointState()
        joints_fb.name=["meca_axis_1_joint",
	  "meca_axis_2_joint",
	  "meca_axis_3_joint",
	  "meca_axis_4_joint",
	  "meca_axis_5_joint",
	  "meca_axis_6_joint"
	]
        while not rospy.is_shutdown():
            try:
                #Robot Status Feedback
                if(self.socket_available):
                    self.socket_available = False           #Block other operations from using the socket while in use
                    robot_status = self.robot.GetStatusRobot()
                    gripper_status = self.robot.GetStatusGripper()
                    self.socket_available = True            #Release the socket so other processes can happen
                    status = UInt8MultiArray()
                    status.data = [
                        robot_status["Activated"],
                        robot_status["Homing"],
                        robot_status["Simulation"],
                        robot_status["Error"],
                        robot_status["Paused"],
                        robot_status["EOB"],
                        robot_status["EOM"],
                        gripper_status["Gripper enabled"],
                        gripper_status["Homing state"],
                        gripper_status["Limit reached"],
                        gripper_status["Error state"],
                        gripper_status["force overload"]
                    ]
                    self.status_publisher.publish(status)

                #Position Feedback
                self.feedback.get_data()
                joints_fb.header.stamp=rospy.Time.now()               
# Philip messing around

                joints_fb.position = [i*3.14159/180. for i in feedback.joints]
                #joints_fb.position = feedback.joints 
                pose_fb = Pose()
                pose_fb.position.x = feedback.cartesian[0]  
                pose_fb.position.y = feedback.cartesian[1] 
                if(len(feedback.cartesian)==4):
                    pose_fb.orientation.x = feedback.cartesian[2] 
                    pose_fb.orientation.y = feedback.cartesian[3] 
                else:
                    pose_fb.position.z = feedback.cartesian[2] 
                    pose_fb.orientation.x = feedback.cartesian[3] 
                    pose_fb.orientation.y = feedback.cartesian[4] 
                    pose_fb.orientation.z = feedback.cartesian[5] 
                self.joint_publisher.publish(joints_fb)
                self.pose_publisher.publish(pose_fb)
            except Exception as error:
                rospy.logerr(str(error))
    
    def __del__(self):
        """Deconstructor for the Mecademic Robot ROS driver
        Deactivates the robot and closes socket connection with the robot
        """
        self.robot.DeactivateRobot()
        self.robot.disconnect()
        self.feedback.disconnect()

if __name__ == "__main__":
    print("main")
    robot = RobotController('192.168.1.100') ### Previously 192.168.0.100 -->> changed to 192.168.1.100
    feedback = RobotFeedback('192.168.1.100','8.1.8')    ### Previously 192.168.0.100 -->> changed to 192.168.1.100
    print("connect")
    robot.connect()
    feedback.connect()
    print("feedback")
    robot.ActivateRobot()
    print("activate")
    robot.home()
    print("Homing completed")
    #robot.SetTRF(0,0,80,0,0,0) # Tool reference frame, w.r.t to Flange (FRF) in mm
    robot.SetBlending(100) # Default is 
    robot.SetCartLinVel(500) # Default is 150 mm/s - Maximum - 1000 mm/s
    robot.SetCartAcc(100) ###### Default is 50% - maximum - 600 % 
    
    #robot.SetVelTimeout(0.40) # velocity timeout set here
    #print('Approximating the TCP points by 50 percentage blending')
    driver = MecademicRobot_Driver(robot, feedback)
    print("spinning")
    rospy.spin()
