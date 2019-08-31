/*
説明
war_stateトピックを読んで使いやすい形に変えて2つのトピックを出力
/red_botまたは/blue_botの名前空間の下で動くようにすること。

　game_state：現在のゲーム状況を記載
　　　string my_color　　　　　：自機の色 redまたはblue
　　　int32 my_points　　　　　：自分の現在の得点
　　　int32 enemys_points　　 ：相手の現在の得点
　　　int32[18] point_state　 ：各点の点数状況 正値：自分の得点、負値：相手の得点、0：中立点(順番は下のpoint_name配列参照)
　state_change：点数状況が変わった直近5点の情報を保持。配列の0番が最直近、以下過去に遡っていく。(cps_list_sizeを変えれば保持数変更可)
　　　time[5] time_stamp　　　：点数が変わったことを認識した時間
　　　int32[5] point_num　　　：点の番号(下のpoint_name配列参照)
　　　string[5] point_name　 ：点の名前
　　　int32[5] point_score　 ：点数状況　正値：自分の得点、負値：相手の得点
*/

#include <iostream>
#include <string>
#include <cstdlib>
#include <cstring>
#include <fstream>
#include <list>
#include "ros/ros.h"
#include "std_msgs/String.h"
#include "state_reader/Change.h"
#include "state_reader/State.h"

const std::string point_name[18] = {"BL_B","BL_L","BL_R","RE_B","RE_L","RE_R",
                                    "Tomato_N","Tomato_S","Omelette_N","Omelette_S",
                                    "Pudding_N","Pudding_S","OctopusWiener_N","OctopusWiener_S",
                                    "FriedShrimp_N","FriedShrimp_E","FriedShrimp_W","FriedShrimp_S"};
const int point_score[18] = {5,5,5,5,5,5,1,1,1,1,1,1,1,1,1,1,1,1};
const int cps_list_size = 5;
std::string my_color; //自機の色
int my_points = 0;    //自分の点数
int enemys_points = 0;//相手の点数
int point[18] = {0};  //各点の点数状況　正値は自分の得点、負値は相手の得点、0は白地
struct change_point_stasus{
  ros::Time time_stamp;
  int c_point_num;             //地点のナンバーpoint_nameの順
  std::string c_point_name;    //地点の名前
  int c_point_score;           //各点の点数状況　正値は自分の得点、負値は相手の得点、0は白地
};
std::list<change_point_stasus> cps_list;



void find_change(){                        //analize_strの後に使う
  ros::Time now_time = ros::Time::now();
  static int privious_point[18] = {0};
  int point_change[18] = {0};
  for (int i = 0; i < 18; i++){
    point_change[i] = point[i] - privious_point[i];
    privious_point[i] = point[i];
    if (point_change[i] != 0){
      change_point_stasus csp;
      csp.time_stamp = now_time;
      csp.c_point_num = i;
      csp.c_point_name = point_name[i];
      csp.c_point_score = point_score[i] * point_change[i] / abs(point_change[i]);
      cps_list.push_front(csp);
      if (cps_list.size() > cps_list_size){
        cps_list.pop_back();
      }
    }
  }
}

int reader(std::string str, std::string key_str, int start_count, int offset, std::string& ans_str){
      int count_key = str.find(key_str, start_count);  //なかった時の処理は？
      //      std::cout<<"find "<< key_str << " at " <<count_key<<std::endl;
      ans_str = str[offset + count_key];
      return count_key;
}

void analize_str(std::string str){  //とても不安定。
    std::string buf;
    std::string hell;     //ゴミ捨て場
    // std::cout<<str<<std::endl;

    //自機の色を取得
    // //なんか自分はredだと思い込んでいるようだ
    // if (reader(str, "players", 0, 22, buf) != -1){
    //   if (buf == "e"){
    //     my_color = "red";
    //   }else if(buf == "y"){
    //     my_color = "blue";
    //   }else{
    //     ROS_ERROR("UNKNOWN COLOR %s", buf.c_str());
    //   }
    // }

    //仕方ないのでparamからとってきてみる
    std::string robot_name;
    ros::NodeHandle pn("~");
    pn.getParam("side", robot_name);
    if(robot_name == "r"){
      my_color = "red";
    }else if(robot_name == "b"){
      my_color = "blue";
    }else{
      ROS_ERROR("UNKNOWN COLOR %s", buf.c_str());
    }
    //自機の色を取得 終わり
    //スコアを取得               2桁ならエラーにならないからOKだろうの精神
    int count_key = str.find("scores");
    buf.clear();
    for (int i = count_key + 20; str[i] != ','; i++){
        buf += str[i];
    }
    if(my_color == "blue"){
      my_points = std::stoi(buf);
    }else if (my_color == "red"){
      enemys_points = std::stoi(buf);
    }
    buf.clear();
    for (int i = count_key + 33; str[i] != '\n'; i++){
        buf += str[i];
    }
    if(my_color == "red"){
      my_points = std::stoi(buf);
    }else if (my_color == "blue"){
      enemys_points = std::stoi(buf);
    }
    //スコアを取得 終わり
    //各点の得点状況を取得
    for(int i = 0; i < 18; i++){
      buf.clear();
      reader(str, "player", reader(str,point_name[i], 0, 0, hell), 10, buf);
      if (buf == "n"){
        point[i] = 0;
      }else if(buf[0] == my_color[0]){
        point[i] = point_score[i];
      }else if(buf == ((my_color == "red") ? "b" : "r")){
        point[i] = -point_score[i];
      }else{
        ROS_ERROR("UNKNOWN COLOR %s", buf.c_str());
      }
      // std::cout<<point[i]<<std::endl;
    }
    //各点の得点状況を取得 終わり
    // std::cout<<my_color<<std::endl;
    // std::cout<<my_points<<std::endl;
    // std::cout<<enemys_points<<std::endl;
}

void state_callback(std_msgs::String str){
  analize_str(str.data);
}

int main(int argc, char** argv){
  ros::init(argc, argv, "state_reader");
  ros::NodeHandle nh;
  ros::Rate rate(10);

  //デバッグ用ファイル読み込み
  // std::ifstream rf;
  // rf.open("/home/light/catkin_ws/src/burger_war/state_reader/src/test.txt", std::ios::in);
  // std::string str;
  // while(!rf.eof()){
  //   std::string buf;
  //   std::getline(rf, buf);
  //   str += (buf + '\n');
  // }
  // analize_str(str);
  //ファイル読み込み終わり

   ros::Subscriber sub = nh.subscribe("war_state", 100, state_callback);
  ros::Publisher pub_change = nh.advertise<state_reader::Change>("state_change",10);
  ros::Publisher pub_state = nh.advertise<state_reader::State>("game_state",10);
  while(ros::ok()){
    ros::spinOnce();

    state_reader::State state;
    state.my_color = my_color;
    state.my_points = my_points;
    state.enemys_points = enemys_points;
    for(int k = 0; k < 18; k++){
      state.point_state[k] = point[k];
    }
    pub_state.publish(state);
    find_change();
    state_reader::Change state_change;
    int i = 0;
    for (auto itr = cps_list.begin(); itr != cps_list.end(); itr++){
      std::cout<<itr->c_point_num<<","<<itr->c_point_name<<","<<itr->c_point_score<<std::endl;
      state_change.time_stamp[i] = itr->time_stamp;
      state_change.point_num[i] = itr->c_point_num;
      state_change.point_name[i] = itr->c_point_name;
      state_change.point_score[i] = itr->c_point_score;
      i++;
    }
    pub_change.publish(state_change);
    rate.sleep();
  }
  return 0;

}
