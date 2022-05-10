#!usr/bin/env
#ROS server use to detect object using KNN classifier
from sklearn.neighbors import KNeighborsClassifier
from knn_classifier.srv import classifier, classifierResponse
from keras.applications.mobilenet import MobileNet
from keras.applications.mobilenet import preprocess_input
from cv_bridge import CvBridge, CvBridgeError
from keras.models import Model
import numpy as np
import rospkg
import rospy
import cv2


def get_image_feature(bgr_image):
  """Extract the features of rgb_image using MobileNet model"""
  print(bgr_image.shape)
  bgr_image= cv2.resize(bgr_image,(224,224))
  print(bgr_image.shape)
  rgb_image = cv2.cvtColor(bgr_image,cv2.COLOR_BGR2RGB)
  resize_img = rgb_image.reshape((1,rgb_image.shape[0],
                                    rgb_image.shape[1],
                                    rgb_image.shape[2]))

  # prepare the image for the MobileNet model
  image = preprocess_input(resize_img)

  model = MobileNet(weights= 'imagenet', input_shape=(224, 224,3))
  model = Model(inputs=model.inputs, outputs=model.layers[-2].output)
  feature = model.predict(image)
  print('Feature shape of an Image: {}'.format(feature.shape))
  return feature


def get_model_feature(file_path):
  """ Load model features from the file """
  with open(file_path, 'rb') as f:
    model_features = np.load(f, allow_pickle=True)
  print('knn_classifier features shape: {}'.format(model_features.shape))
  return model_features


def remove_labels(model_features):
  """Removes the class_ids from the loaded feature file, class_id
     exists at the end of each row  """
  formated_data = []
  labels = []
  for z in model_features:
    fix_data = z[:-1]
    clip_label = z[-1]
    labels.append(clip_label)
    formated_data.append(fix_data)
  labels_list = np.array(labels)
  formated_data = np.array(formated_data)
  print('Resized Feature Vector: {} '.format(formated_data.shape))
  return formated_data, labels_list


def reshape_label_array(feature_data, label_list):
  """Label list is reshaped (dataset size, number of classes)"""
  no_classes = 59
  rows, columns = feature_data.shape
  label_length= no_classes * rows
  loaded_labels= [0] * label_length
  loaded_labels= np.array(loaded_labels)
  reshaped_label = np.reshape(loaded_labels,(-1,no_classes))

  for count,j in enumerate(label_list):
    reshaped_label[count][int(j)]= 1
  print('Reshaped Label Array: {} '.format(reshaped_label.shape))
  return reshaped_label

def knn_classifier(model_features, image_feature, label_arr):
  """Use KNN classifier to predict
    returns: predicted class_id and confidence of each class"""
  classifier_model = KNeighborsClassifier(n_neighbors=3)
  classifier_model.fit(model_features,label_arr)
  y_pred = classifier_model.predict(image_feature)
  confidence = classifier_model.predict_proba(image_feature)
  class_confidence=[]
  confidence= list(confidence)
  print(y_pred)
  for x in confidence:
    class_confidence.append(x[0][1])
  print('Class_id: {} '.format(y_pred[0]))
  print(np.where(y_pred==1))
  return y_pred[0], class_confidence


def shutdown_fun():
  print('shutting down')


def handle_request(request):
  """This method is called when a service request is received"""

  # Load data from service request
  ros_rgb_image   = request.rgb

  # Convert images to openCV
  cv_rgb_image   = None
  bridge = CvBridge()

  try:
    cv_rgb_image = bridge.imgmsg_to_cv2(ros_rgb_image)
  except CvBridgeError as e:
    print(e)
  
  rospack = rospkg.RosPack()
  package_path = rospack.get_path('knn_classifier')
  img_feature = get_image_feature(cv_rgb_image)

  path = package_path + '/scripts/features.npy'
  feature_data = get_model_feature(path)

  formated_data, classes = remove_labels(feature_data)

  reshaped_label = reshape_label_array(formated_data, classes)

  class_id, confidence = knn_classifier(formated_data, img_feature, reshaped_label)


  response= classifierResponse()
  response.class_ids = list(class_id)
  response.success = True
  response.class_confidence = list(confidence)
  return response


def classifier_server():
  rospy.init_node('classifier')
  s= rospy.Service('classifier', classifier, handle_request)
  rospy.on_shutdown(shutdown_fun)
  print('Ready to accept image')
  print(s)
  rospy.spin()



if __name__ == '__main__':
  #classifier('/tmp/features.npy')
  try:
    classifier_server()
  except rospy.ROSInterruptException:
    pass