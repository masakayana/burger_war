#!/usr/bin/env python
# -*- coding: utf-8 -*-
import rospy
import random

from geometry_msgs.msg import Twist
from state_reader.msg import State
from state_reader.msg import Change
from find_green.msg import Marker
#from std_msgs.msg import String
#from sensor_msgs.msg import Image
#from cv_bridge import CvBridge, CvBridgeError
#import cv2
import tf


import actionlib
from move_base_msgs.msg import MoveBaseAction, MoveBaseGoal, MoveBaseActionGoal
from geometry_msgs.msg import Vector3, PoseWithCovarianceStamped
import actionlib_msgs


class RandomBot():
    def __init__(self, bot_name):
        self.name = rospy.get_param("~robot_name")
        self.color = rospy.get_param("~side")
        # velocity publisher
        self.vel_pub = rospy.Publisher('cmd_vel', Twist,queue_size=1)
        self.client = actionlib.SimpleActionClient('move_base',MoveBaseAction)
        self.my_posi = []
        self.my_place = 0
        self.enemy_place = 0
        self.now_point_num = 0
        self.now_point_score = 0
        self.pre_point_num = 0
        self.pre_point_score = 0
        self.point_counter = 0
        self.pre_time_stamp = rospy.Time.now()
        self.NORTH = 1
        self.EAST = 2
        self.SOUTH = 3
        self.WEST = 4
        self.LEFT = 5
        self.RIGHT = 6
        self.ON = 1
        self.OFF = 0
        self.navi_flag = self.ON # ナビゲーションで動いているか、適当に動いているか
        self.find_green_flag = self.OFF # 敵を見つけたとき1、その他0
        self.green_dis = 0
        self.green_center_x = 0
        self.pre_green_center_x = 0
        self.Atack_Direction = 0
        self.Atack_counter = 0

        self.state = 0
        self.counter = 0

        # # 状態データ;
        self.cvtest_sub = rospy.Subscriber('state_change', Change, self.stChangeCallback)     #←これを追加
#        self.cvtest_sub = rospy.Subscriber("move_base/goal", MoveBaseActionGoal, self.goal_callback)  #相対に変更
        self.cvtest_sub = rospy.Subscriber("amcl_pose", PoseWithCovarianceStamped, self.my_place_callback)  #相対に変更
        self.cvtest_sub = rospy.Subscriber("find_green", Marker, self.find_green_callback)


    def my_place_callback(self, data):
        pos = data.pose.pose
        e = tf.transformations.euler_from_quaternion((pos.orientation.x, pos.orientation.y, pos.orientation.z, pos.orientation.w))
        self.my_posi = [pos.position.x, pos.position.y, e[2]]
        print "my place ({0},{1},{2}),".format  (self.my_posi[0],self.my_posi[1],self.my_posi[2])
        if self.my_posi[0] > self.my_posi[1]:
            if self.my_posi[0] > -self.my_posi[1]:
                self.my_place = self.NORTH #place_N
            else :
                self.my_place = self.EAST #place_E
        else :
            if self.my_posi[0] > -self.my_posi[1]:
                self.my_place = self.WEST #place_W
            else :
                self.my_place = self.SOUTH #place_S
        print "my_place=",self.my_place

    # ### 状態データTopic Subscribe時のCallback関数
    def stChangeCallback(self, data):
        self.now_point_num = data.point_num[0]
        self.now_point_score = data.point_score[0]

        if data.point_score[0] < 0 and (self.now_point_num != self.pre_point_num or self.now_point_score != self.pre_point_score): # 敵が得点を得た時
            if data.point_name[0] == "Tomato_N" \
               or data.point_name[0] == "Omelette_N" \
               or data.point_name[0] == "FriedShrimp_N" :
                self.enemy_place = self.NORTH #place_N
            elif data.point_name[0] == "Tomato_S" \
               or data.point_name[0] == "FriedShrimp_W" \
               or data.point_name[0] == "Pudding_N" :
                self.enemy_place = self.WEST #place_W
            elif data.point_name[0] == "Omelette_S" \
               or data.point_name[0] == "FriedShrimp_E" \
               or data.point_name[0] == "OctopusWiener_N" :
                self.enemy_place = self.EAST #place_E
            elif data.point_name[0] == "Pudding_S" \
               or data.point_name[0] == "FriedShrimp_S" \
               or data.point_name[0] == "OctopusWiener_S" :
                self.enemy_place = self.SOUTH #place_S
            elif data.point_name[0] == "RE_L" \
               or data.point_name[0] == "BL_L" :
                self.enemy_place = self.LEFT #左側ポイントを取られた！
                self.client.cancel_all_goals()   #最初にgoalをキャンセルして、黙らせる
            elif data.point_name[0] == "RE_R" \
               or data.point_name[0] == "BL_R" :
                self.enemy_place = self.RIGHT #右側ポイントを取られた！
                self.client.cancel_all_goals()   #最初にgoalをキャンセルして、黙らせる
            # 敵と自分の位置から状況を判断
            # 敵が反対側のエリア　無視
            if abs(my_place - enemy_place) == 2:
                print("enemy is opposite.\nI don't move.")
            # 敵が同じエリア　下手に動かない。　無視
            elif abs(my_place - enemy_place) == 0:
                print("enemy is in the same zone.\nI don't move.")
            # 敵が反時計回り方向の隣のエリア
            elif (my_place - enemy_place == -1) or (my_place - enemy_place == 3):
                self.client.cancel_all_goals()   #最初にgoalをキャンセルして、黙らせる
                print "I should move to CCW",
            # 敵が時計回り方向の隣のエリア
            elif (my_place - enemy_place == 1) or (my_place - enemy_place == -3):
                self.client.cancel_all_goals()   #最初にgoalをキャンセルして、黙らせる
                print "I should move to CW",
            # 移動位置計算終わり

    def get_point_object_in_order(self):
        point_order_for_r = [17,19,16,10,7,21,15,12,9]
        # point_order_for_r = [17,11,16,10,7,13,15,12,9,14,8,6]
        point_order_for_b = [14,18,15,9,12,20,16,7,10]
        # point_order_for_b = [14,8,15,9,12,6,16,7,10,17,11,13]
        angle_degree = 40
        point_order = 0
        target_position_x = [0,0,0,0,0,0, 0.9, 0.0,  0.9,  0.0,-0.0,-0.9, -0.0,  -0.9,0.45,   0.0,   0.0,-0.45,0.7,-0.7,0.7,-0.7]
        target_position_y = [0,0,0,0,0,0,0.43,0.60,-0.43,-0.60,0.60,0.43,-0.60, -0.43,0.0,  -0.60,   0.60, 0.0,0.0,0.0,0.0,0.0]
        target_orientation_yaw = [0,0,0,0,0,0,angle_degree/180*3.14,   0,-angle_degree/180*3.14,    0,   3.14,3.14-angle_degree/180*3.14,    3.14,3.14+angle_degree/180*3.14,  3.14, 1.57, -1.57,   0, 3.14,0,1.57,-1.57]
        if (self.point_counter < 9):
            if (self.color == "r"):
                point_order = point_order_for_r[self.point_counter]
            elif (self.color == "b"):
                point_order = point_order_for_b[self.point_counter]
            self.point_counter += 1
            self.setGoal(target_position_x[point_order], target_position_y[point_order], target_orientation_yaw[point_order])
        else:
            self.point_counter = 0

    def find_green_callback(self, data):
        if data.est_dis == 0:    #値が入っていないので無視。
            return None
        else: # 値が入っている時は、追跡
            self.client.cancel_all_goals()   #最初にgoalをキャンセルして、黙らせる
	    self.state == 'find'
            self.green_dis = data.est_dis
            self.pre_green_center_x = self.green_center_x
            self.green_center_x = data.center_x

    def setGoal(self,x,y,yaw):
        self.client.wait_for_server()

        goal = MoveBaseGoal()
        goal.target_pose.header.frame_id = self.name + "/map"
        goal.target_pose.header.stamp = rospy.Time.now()
        goal.target_pose.pose.position.x = x
        goal.target_pose.pose.position.y = y

        # Euler to Quartanion
        q=tf.transformations.quaternion_from_euler(0,0,yaw)
        goal.target_pose.pose.orientation.x = q[0]
        goal.target_pose.pose.orientation.y = q[1]
        goal.target_pose.pose.orientation.z = q[2]
        goal.target_pose.pose.orientation.w = q[3]

        self.client.send_goal(goal)
        wait = self.client.wait_for_result()
        if not wait:
            rospy.logerr("Action server not available!")
            rospy.signal_shutdown("Action server not available!")
        else:
            return self.client.get_result()

    def move_search_point(self, my_place, enemy_place):
        # 敵発見時の移動位置設定
        list_move_point     = [ "ne",   "es",   "sw",   "wn"]
        list_move_point_x   = [0.325, -0.325, -0.325,  0.325]
        list_move_point_y   = [-0.325,  -0.325, 0.325, 0.325]
        list_move_point_yaw = [0.349, -0.349, -2.79, 2.79]

        # 不正値チェック
        if my_place == 0 or my_place > 4:
            print("No or illegal data in my_place.",my_place)
            return False
        if enemy_place == 0 or enemy_place > 6:
            print("No or illegal data in enemy_place.",enemy_place)
            return False
        # 不正値チェック終わり
        # 移動位置計算
        if self.state == 'find':
            print("Find enemy!")
        # 自分車体の左側のポイントを取られてしまった。
        elif enemy_place == self.LEFT:
            self.state = 'stop'
            self.counter = 32 # 左回転
            twist = self.calcTwist() # 各状態での動作指令値設定
            navi_flag = self.OFF
        # 自分車体の右側のポイントを取られてしまった。
        elif enemy_place == self.RIGHT:
            self.state = 'stop'
            self.counter = 31 # 右回転
            navi_flag = self.OFF
        # 敵が反対側のエリア　無視
        elif abs(my_place - enemy_place) == 2:
            print("enemy is opposite.\nI don't move.")
            self.get_point_object_in_order()
            navi_flag = self.ON
        # 敵が同じエリア　下手に動かない。　無視
        elif abs(my_place - enemy_place) == 0:
            print("enemy is in the same zone.\nI don't move.")
            self.get_point_object_in_order()
            navi_flag = self.ON
       # 敵が半時計回り方向の隣のエリア
        elif (my_place - enemy_place == -1) or (my_place - enemy_place == 3):
            move_point     = list_move_point[my_place - 1]
            move_point_x   = list_move_point_x[my_place - 1]
            move_point_y   = list_move_point_y[my_place - 1]
            move_point_yaw = list_move_point_yaw[my_place - 1] + 3.14
            print "I should move to",
            print(move_point, move_point_x, move_point_y, move_point_yaw)
            self.setGoal(move_point_x, move_point_y, move_point_yaw)
            # 首振り設定
            self.state = 'stop'
            self.counter = 31 # 右回転
            navi_flag = self.OFF
        # 敵が時計回り方向の隣のエリア
        elif (my_place - enemy_place == 1) or (my_place - enemy_place == -3):
            move_point     = list_move_point[enemy_place - 1]
            move_point_x   = list_move_point_x[enemy_place - 1]
            move_point_y   = list_move_point_y[enemy_place - 1]
            move_point_yaw = list_move_point_yaw[enemy_place - 1]
            print "I should move to",
            print(move_point, move_point_x, move_point_y, move_point_yaw)
            self.setGoal(move_point_x, move_point_y, move_point_yaw)
            # 首振り設定
            self.state = 'stop'
            self.counter = 32 # 左回転
            navi_flag = self.OFF
        else:
            if navi_flag == self.ON: # ナビゲーションがONの時
                self.get_point_object_in_order()
            else: # ナビゲーションがオフの時
                twist = self.calcTwist() # 各状態での動作指令値設定
                self.vel_pub.publish(twist)

        # 移動位置計算終わり


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

        #敵を追跡
        elif self.state == 'find':
            if abs(data.center_x) < 60:    #ほぼ真ん中にいたら前進しながら曲がりましょう
                #敵の速度から攻撃方向を見定める
                if self.Atack_counter < 3:
                    x = 0.0
                    th = 0.0
                    self.Atack_Direction = self.pre_green_center_x - self.green_center_x
                    self.Atack_counter += 1
                #攻撃開始！
#                elif self.Atack_counter >= 3:
                else:
                    #敵が右に動いている時 敵が画面左側(-0.3)の位置にいるようにしながら接近
                    if self.Atack_Direction >= 0:
                        x = 0.2
                        th = -1 * (self.green_center_x + 0.3)
                    #敵が左に動いている時 敵が画面左側(0.3)の位置にいるようにしながら接近
                    else:
                        x = 0.2
                        th = -1 * (self.green_center_x - 0.3)
            else:      #端っこならとりあえず回りましょう
                x = 0.0
                th = -0.2 * self.green_center_x / abs(self.green_center_x)

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

    def strategy1(self):
        r = rospy.Rate(100) # change speed 1fps
        while not rospy.is_shutdown():
            self.move_search_point(self.my_place,self.enemy_place) # 敵の位置判定と状態設定、ナビ動作
            self.pre_point_num = self.now_point_num
            self.pre_point_score = self.now_point_score

            r.sleep()


if __name__ == '__main__':
    rospy.init_node('random_run')
    bot = RandomBot('Random')
    bot.strategy1()
