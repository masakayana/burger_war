#include <iostream>
#include <vector>
#include "ros/ros.h"
#include <sensor_msgs/image_encodings.h>
#include <find_green/Marker.h>
#include <image_transport/image_transport.h>
#include <cv_bridge/cv_bridge.h>
#include <opencv2/imgproc/imgproc.hpp>
#include <opencv2/highgui/highgui.hpp>

#define MINIMUM_AREA 500
static const std::string OPENCV_WINDOW = "Image Window";

class image_converter{
private:
  ros::NodeHandle nh;
  ros::Publisher pub;
  image_transport::ImageTransport it;
  image_transport::Subscriber image_sub;
  image_transport::Publisher image_pub;

public:
  image_converter():it(nh){
    pub = nh.advertise<find_green::Marker>("find_green",10);
    image_sub = it.subscribe("image_raw", 1, &image_converter::imageCb, this);
    cv::namedWindow(OPENCV_WINDOW+" lower_falf_img");
    cv::namedWindow(OPENCV_WINDOW+" image");
  }

  ~image_converter(){
    cv::destroyWindow(OPENCV_WINDOW+" lower_falf_img");
    cv::destroyWindow(OPENCV_WINDOW+" image");
  }

  void imageCb(const sensor_msgs::ImageConstPtr& msg){
    cv_bridge::CvImagePtr cv_ptr;
    try{
      cv_ptr = cv_bridge::toCvCopy(msg, sensor_msgs::image_encodings::BGR8);
    }
    catch(cv_bridge::Exception& e){
      ROS_ERROR("%s",e.what());
      return;
    }
    cv::Mat channel[3], green, blue, red, img;
    cv::split(cv_ptr->image, channel);
    blue  = channel[0];
    green = channel[1];
    red   = channel[2];
    //いろいろ画像処理 (緑の部分を抜き出し、下2/3に切り取り、2値化)
    bitwise_or(blue,red,img);
    bitwise_not(img,img);
    bitwise_and(green,img,img);
    cv::Mat lower_falf_img(img, cv::Rect(0, img.rows / 3, img.cols, img.rows * 2 / 3));
    cv::threshold(lower_falf_img, lower_falf_img, 90, 255, CV_THRESH_BINARY);
    // cv::GaussianBlur(lower_falf_img, lower_falf_img, cv::Size(9, 9), 2, 2);
    //いろいろ画像処理　終わり
    //輪郭検知
    std::vector<std::vector<cv::Point> > contours;
    cv::findContours(lower_falf_img, contours, CV_RETR_EXTERNAL, CV_CHAIN_APPROX_NONE);
    double max_area = 0;
    int max_i = 0;
    for(int i = 0; i < contours.size(); i++){
      double area = cv::contourArea(contours.at(i));
      if (area > max_area){
        max_area = area;
        max_i = i;
      }
    }
    //輪郭検知終わり
    //publish関連作業
    if (max_area > MINIMUM_AREA){
      int count = contours[max_i].size();
      double x = 0;
      double max_x = 0;
      double min_x = 1000;
      double y = 0;
      double max_y = 0;
      double min_y = 1000;
      for (int i = 0; i < count; i++){
        x += contours[max_i][i].x;
        if (max_x < contours[max_i][i].x) max_x = contours[max_i][i].x;
        if (min_x > contours[max_i][i].x) min_x = contours[max_i][i].x;
        y += contours[max_i][i].y;
        if (max_y < contours[max_i][i].y) max_y = contours[max_i][i].y;
        if (min_y > contours[max_i][i].y) min_y = contours[max_i][i].y;
      }
      x /= count;
      x = x - img.cols / 2;  //画像中心を0にする。
      y /= count;            //どうせあんまり使わないのでそのままで。
      double length_x = max_x - min_x;
      double length_y = max_y - min_y;
      double estimated_distance = std::pow(length_y, -0.883) * 38.532;  //(m) 適当ふぃってぃんぐ　estimated_distance = 38.532*length_y^(-0.883) y方向に一部が隠れることはないはず
      std::cout<<"center: "<<x<<", "<<y<<std::endl;
      std::cout<<"length: "<<length_x<<", "<<length_y<<std::endl;
      std::cout<<"distance: "<<estimated_distance<<std::endl;
      find_green::Marker pub_info;
      pub_info.time_stamp = ros::Time::now();
      pub_info.center_x   = x;
      pub_info.center_y   = y;
      pub_info.width      = length_x;
      pub_info.height     = length_y;
      pub_info.est_dis    = estimated_distance;
      pub.publish(pub_info);
    }
    //publish関連作業終わり
    //表示するだけ
    cv::imshow(OPENCV_WINDOW+" lower_falf_img", lower_falf_img);
    cv::imshow(OPENCV_WINDOW+" image", cv_ptr->image);
    cv::waitKey(3);
  }
};

int main(int argc, char** argv){
  ros::init(argc, argv, "find_green");
   image_converter ic;
   ros::spin();
  return 0;
}
