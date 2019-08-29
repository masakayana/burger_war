#!/usr/bin/env python
# -*- coding: utf-8 -*-
# enemy.py
# write by yamaguchi takuya @dashimaki360
#
# Enemy "SIO ONIGIRI" sorce code for One month ROBOCON
# SIO strategy 
## GO and Back only


import rospy
import random

from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from sensor_msgs.msg import JointState
#from state_reader.msg import State

class gurakoro():
    def __init__(self, bot_name):
        # bot name 
        self.name = bot_name
	#counter
	self.counter = 0
        # robot state 'go' or 'back'
        self.state = 'go' 
        # robot wheel rot 
        self.wheel_rot_r = 0
        self.wheel_rot_l = 0
        self.pose_x = 0
        self.pose_y = 0
	self.point_state = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

        # speed [m/s]
        self.speed = 0.35
	self.angular_speed = 1.0
        # publisher
        self.vel_pub = rospy.Publisher('cmd_vel', Twist,queue_size=1)
        # subscriber
        self.odom_sub = rospy.Subscriber('odom', Odometry, self.odomCallback)
        self.odom_sub = rospy.Subscriber('joint_states', JointState, self.jointstateCallback)
	# self.state_sub = rospy.Subscriber('game_state', State, self.stateCallback)

    def odomCallback(self, data):
        '''
        Dont use odom in this program now
        update robot pose in gazebo
        '''
        self.pose_x = data.pose.pose.position.x
        self.pose_y = data.pose.pose.position.y

    #def stateCallback(self, data):
    #    self.point_state = data.point_state

    def jointstateCallback(self, data):
        '''
        update wheel rotation num
        '''
        self.wheel_rot_r = data.position[0]
        self.wheel_rot_l = data.position[1]

    def calcTwist(self):
        '''
        calc twist from self.state
        'go' -> self.speed,  'back' -> -self.speed
        '''
        if self.state == 'go':
            x = self.speed
	    th = 0
        elif self.state == 'back':
            x = -self.speed
            th = 0
        elif self.state == 'migi':
            x = 0
            th = -self.angular_speed
        elif self.state == 'hidari':
            x = 0
            th = self.angular_speed
	elif self.state == 'naname_hidari':
            x = 0.6 * self.speed
            th = self.angular_speed
	elif self.state == 'naname_migi_back':
            x = -0.4 * self.speed
            th = self.angular_speed

        elif self.state == 'stop':
            x = 0
            th = 0
        else:
            # error state
            x = 0
            th = 0
            rospy.logerr("Gurakoro state is invalid value %s", self.state)

        twist = Twist()
        twist.linear.x = x; twist.linear.y = 0; twist.linear.z = 0
        twist.angular.x = 0; twist.angular.y = 0; twist.angular.z = th
        return twist

    def calcState(self):
        '''
        update robot state 'go' or 'back'
        '''
        if self.counter == 0 and self.wheel_rot_r < 27:
            self.state = 'go'
	elif self.counter == 0:
 	    self.state = 'stop'
            self.counter = 1

        if self.counter == 1 and self.wheel_rot_r > 15:
            self.state = 'back'
        elif self.counter == 1:
	    self.state = 'stop'
            self.counter = 2

	if self.counter == 2 and self.wheel_rot_r - self.wheel_rot_l < 4:
	    self.state = 'hidari'
	elif self.counter == 2:
	    self.state = 'stop'
	    self.counter = 3

	if self.counter == 3 and self.wheel_rot_r < 22:
	    self.state = 'go'
	elif self.counter == 3:
	    self.state = 'stop'
            self.counter = 4

	if self.counter == 4 and self.wheel_rot_r > 16:
            self.state = 'back'
	elif self.counter == 4:
	    self.state = 'stop'
	    self.counter = 5

	if self.counter == 5 and self.wheel_rot_l - self.wheel_rot_r < 3.5:
	    self.state = 'migi'
	elif self.counter == 5:
	    self.state = 'stop'
	    self.counter = 6

	if self.counter == 6 and self.wheel_rot_r < 20:
            self.state = 'go'
	elif self.counter == 6:
	    self.state = 'stop'
	    self.counter = 7

	if self.counter == 7 and self.wheel_rot_r > 16:
            self.state = 'back'
	elif self.counter == 7:
            print( self.point_state[6], self.point_state[8])
    	    self.state = 'stop'
            self.counter = 8

	if self.counter == 8 and self.wheel_rot_r - self.wheel_rot_l < 3:
            self.state = 'hidari'
	elif self.counter == 8:
	    self.state = 'stop'
	    self.counter = 9

	if self.counter == 9 and self.wheel_rot_r < 47:
            self.state = 'go'
	elif self.counter == 9:
	    self.state = 'stop'
	    self.counter = 10

	if self.counter == 10 and self.wheel_rot_l - self.wheel_rot_r < 15:
            self.state = 'migi'
	elif self.counter == 10:
	    self.state = 'stop'
	    self.counter = 11

	if self.counter == 11 and self.wheel_rot_l - self.wheel_rot_r > 12:
            self.state = 'naname_migi_back'
	elif self.counter == 11:
	    self.state = 'stop'
	    self.counter = 12

	if self.counter == 12 and self.wheel_rot_l - self.wheel_rot_r > 5:
            self.state = 'hidari'
	elif self.counter == 12:
	    self.state = 'stop'
	    self.counter = 13

	if self.counter == 13 and self.wheel_rot_r < 60:
            self.state = 'go'
	elif self.counter == 13:
    	    self.state = 'stop'
	    self.counter = 14

	if self.counter == 14 and self.wheel_rot_l - self.wheel_rot_r < 15:
            self.state = 'migi'
	elif self.counter == 14:
	    self.state = 'stop'
	    self.counter = 15

	if self.counter == 15 and self.wheel_rot_r > 50:
            self.state = 'back'
	elif self.counter == 15:
	    self.state = 'stop'
	    self.counter = 16

	if self.counter == 16 and self.wheel_rot_l - self.wheel_rot_r > 11:
            self.state = 'hidari'
	elif self.counter == 16:
	    self.state = 'stop'
	    self.counter = 17

	if self.counter == 17 and  self.wheel_rot_r < 55:
            self.state = 'go'
	elif self.counter == 17:
	    self.state = 'stop'
	    self.counter = 18

	if self.counter == 18 and self.wheel_rot_r > 50:
            self.state = 'back'
	elif self.counter == 18:
	    self.state = 'stop'
	    self.counter = 19

        if self.counter == 19 and self.wheel_rot_l - self.wheel_rot_r < 17:
            self.state = 'migi'
	elif self.counter == 19:
	    self.state = 'stop'
	    self.counter = 20

	if self.counter == 20 and self.wheel_rot_r < 49:
            self.state = 'go'
	elif self.counter == 20:
	    self.state = 'stop'
	    self.counter = 21

	if self.counter == 21 and self.wheel_rot_r > 48:
            self.state = 'back'
	elif self.counter == 21:
	    self.state = 'stop'
	    self.counter = 22

	if self.counter == 22 and  self.wheel_rot_l - self.wheel_rot_r > 11:
            self.state = 'hidari'
	elif self.counter == 22:
	    self.state = 'stop'
	    self.counter = 23

	if self.counter == 23 and self.wheel_rot_r < 85:
            self.state = 'go'
	elif self.counter == 23:
	    self.state = 'stop'
	    self.counter = 24

	if self.counter == 24 and self.wheel_rot_l - self.wheel_rot_r < 28:
            self.state = 'migi'
	elif self.counter == 24:
	    self.state = 'stop'
	    self.counter = 25

	if self.counter == 25 and  self.wheel_rot_l - self.wheel_rot_r > 19:
            self.state = 'hidari'
	elif self.counter == 25:
	    self.state = 'stop'
	    self.counter = 26

	if self.counter == 26 and self.wheel_rot_r < 115:
            self.state = 'go'
	elif self.counter == 26:
	    self.state = 'stop'
	    self.counter = 27

	if self.counter == 27 and self.wheel_rot_l - self.wheel_rot_r < 30:
            self.state = 'migi'
	elif self.counter == 27:
	    self.state = 'stop'
	    self.counter = 28

	if self.counter == 28 and self.wheel_rot_r > 105:
            self.state = 'back'
	elif self.counter == 28:
	    self.state = 'stop'
	    self.counter = 29

	if self.counter == 29 and self.wheel_rot_l - self.wheel_rot_r < 35:
            self.state = 'migi'
	elif self.counter == 29:
	    self.state = 'stop'
	    self.counter = 30

	if self.counter == 30 and self.wheel_rot_l - self.wheel_rot_r > 25:
            self.state = 'hidari'
	elif self.counter == 30:
	    self.state = 'stop'
	    self.counter = 29

    def strategy(self):
        '''
        calc Twist and publish cmd_vel topic
        Go and Back loop forever
        '''
        r = rospy.Rate(5) # change speed 1fps

        while not rospy.is_shutdown():
            # update state from now state and wheel rotation
            self.calcState()
            # update twist
            twist = self.calcTwist()

            # publish twist topic
            self.vel_pub.publish(twist)

            r.sleep()


if __name__ == '__main__':
    rospy.init_node('gurakoro')
    bot = gurakoro('gurakoro')
    bot.strategy()

