#!/usr/bin/env python

# Written mainly for python2, as this client might be used 
# to test the service calls from a older system with older ROS distribution
from __future__ import print_function
import sys
import rospy
import rospkg
import cv2
from knn_classifier.srv import classifier
from cv_bridge import CvBridge, CvBridgeError
from std_msgs.msg import String

service_name = "classifier"

def image_service_client():
    try:
        # Load images from data dir
        rospack = rospkg.RosPack()
        package_path = rospack.get_path('knn_classifier')
        data_path = package_path + '/data/partial_views/VollMilch/'
        cv_rgb_image = cv2.imread(data_path + 'VollMilch_30_1_crop.png')
       

        if cv_rgb_image is None:
            print("Couldn't load cv_rgb_image at " + data_path)
            sys.exit(1)

        bridge = CvBridge()
        ros_rgb_image = None
        try:
            ros_rgb_image = bridge.cv2_to_imgmsg(cv_rgb_image, encoding="passthrough")
        except CvBridgeError as e:
            print(e)

        str_msg = String("description")

        print("Waiting for service to come up...")
        rospy.wait_for_service(service_name)
        im_service_client = rospy.ServiceProxy(service_name, classifier)
        print("Calling service")
        response = im_service_client(ros_rgb_image, str_msg)
        print(response)
        return response.success
    except rospy.ServiceException as e:
        print("Service call failed: %s"%e)

if __name__ == "__main__":
    print("Sending service request to " + service_name)
    image_service_client()