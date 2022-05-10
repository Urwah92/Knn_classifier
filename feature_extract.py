"""Example of using the MobileNet model as a feature extraction"""
from keras.applications.mobilenet import MobileNet
from keras.models import Model
from keras.preprocessing.image import ImageDataGenerator
import numpy as np
import os


def set_dataset_dir(label_base_dir, label_dir):
    """This function is used to delete all text files and non-RGB files from the dataset directory."""
    labels = []
    total = []
    for i in label_base_dir:
        tmp = os.listdir(label_dir + "/" + i)
        label = [str(i)] * len(tmp)
        labels.append(label)
    for j in label_base_dir:
        images = os.listdir(label_dir + '/' + j)
        for i in images[0:]:
            path = label_dir + '/' + j + '/' + i
            total.append(i)
            if i.endswith('.txt'):
                os.remove(path)
            elif i.endswith('depthcrop.png'):
                os.remove(path)
            elif i.endswith('mask.png'):
                os.remove(path)


def get_model():
    """This method is used to create a keras model and eliminates the model's final layer."""
    model = MobileNet(weights='imagenet', input_shape=(224, 224, 3))
    # remove the output layer
    model.summary()
    model = Model(inputs=model.inputs, outputs=model.layers[-2].output)
    return model


def get_from_train_datagen(data, i):
    """This method is use to extract x,y from the datagen object."""
    z = []
    for u in range(len(data)):
        for v in data[u][i]:
            z.append(v)
    return np.array(z)


def train_datagenerator():
    """This method gets training object using ImageDataGenerator()"""
    train_datagen = ImageDataGenerator()
    train = train_datagen.flow_from_directory(label_dir, class_mode='categorical', batch_size=500,
                                              target_size=(224, 224))
    return train


def add_labels_with_features(features):
    """This method appends label indices at the end of each image array."""
    tmp2 = []
    tmp_var = []
    feature_x, feature_y = features.shape
    result = np.where(y == 1)
    for count, f in enumerate(features):
        tmp_var = np.append(f, result[1][count])
        tmp2 = np.append(tmp2, tmp_var)

    final_array = np.array(tmp2)
    final_array = np.reshape(final_array, (feature_x, feature_y + 1))
    print('Reshaped feature array with labels: ', final_array.shape)
    return final_array


#Dataset path
label_dir = "/home/rs2004/knn_ws/src/knn_classifier/data/partial_views"
label_base_dir = os.listdir(label_dir)

#Saved file path
save_file_path= "/home/rs2004/knn_ws/src/knn_classifier/scripts/features.npy"

set_dataset_dir(label_base_dir,label_dir)

model = get_model()
train = train_datagenerator()
x = get_from_train_datagen(train, 0)
y = get_from_train_datagen(train, 1)

print('Array y:', y.shape)
print('Array x:', x.shape)

features = model.predict(x, batch_size=500)
print('Predicted Features shape: ', features.shape)

set_features = add_labels_with_features(features)
with open(save_file_path, 'wb') as f:
  np.save(f, set_features)

