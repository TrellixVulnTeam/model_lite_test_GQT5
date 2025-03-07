
# coding: utf-8

# Deep Learning Models -- A collection of various deep learning architectures, models, and tips for TensorFlow and PyTorch in Jupyter Notebooks.
# - Author: Sebastian Raschka
# - GitHub Repository: https://github.com/rasbt/deeplearning-models

# In[1]:




# # Model Zoo -- Convolutional Autoencoder with Nearest-neighbor Interpolation

# A convolutional autoencoder using nearest neighbor upscaling layers that compresses 768-pixel MNIST images down to a 7x7x4 (196 pixel) representation.

# In[2]:


import tensorflow as tf
from tensorflow.examples.tutorials.mnist import input_data


##########################
### DATASET
##########################

mnist = input_data.read_data_sets("./", validation_size=0)


##########################
### SETTINGS
##########################

# Hyperparameters
learning_rate = 0.001
training_epochs = 5
batch_size = 128

# Architecture
input_size = 784
image_width = 28

# Other
print_interval = 200
random_seed = 123


##########################
### GRAPH DEFINITION
##########################

g = tf.Graph()
with g.as_default():
    
    tf.set_random_seed(random_seed)

    # Input data
    tf_x = tf.placeholder(tf.float32, [None, input_size], name='input')
    input_layer = tf.reshape(tf_x, shape=[-1, image_width, image_width, 1])

    ###########
    # Encoder
    ###########
    
    # 28x28x1 => 28x28x8
    conv1 = tf.layers.conv2d(input_layer, filters=8, kernel_size=(3, 3),
                             strides=(1, 1), padding='same', 
                             activation=tf.nn.relu)
    
    # 28x28x8 => 14x14x8
    maxpool1 = tf.layers.max_pooling2d(conv1, pool_size=(2, 2), 
                                       strides=(2, 2), padding='same')
    
    # 14x14x8 => 14x14x4
    conv2 = tf.layers.conv2d(maxpool1, filters=4, kernel_size=(3, 3), 
                             strides=(1, 1), padding='same', 
                             activation=tf.nn.relu)
    
    # 14x14x4 => 7x7x4
    encode = tf.layers.max_pooling2d(conv2, pool_size=(2, 2), 
                                     strides=(2, 2), padding='same', 
                                     name='encoding')

    ###########
    # Decoder
    ###########
    
    # 7x7x4 => 14x14x4
    deconv1 = tf.image.resize_nearest_neighbor(encode, 
                                               size=(14, 14))
    # 14x14x4 => 14x14x8
    conv3 = tf.layers.conv2d(deconv1, filters=8, kernel_size=(3, 3), 
                             strides=(1, 1), padding='same', 
                             activation=tf.nn.relu)
    
    # 14x14x8 => 28x28x8
    deconv2 = tf.image.resize_nearest_neighbor(conv3, 
                                               size=(28, 28))
    # 28x28x8 => 28x28x8
    conv4 = tf.layers.conv2d(deconv2, filters=8, kernel_size=(3, 3), 
                             strides=(1, 1), padding='same', 
                             activation=tf.nn.relu)
    # 28x28x8 => 28x28x1
    logits = tf.layers.conv2d(conv4, filters=1, kernel_size=(3,3), 
                              strides=(1, 1), padding='same', 
                              activation=None)
    
    decode = tf.nn.sigmoid(logits, name='decoding')

    ##################
    # Loss & Optimizer
    ##################
    
    loss = tf.nn.sigmoid_cross_entropy_with_logits(labels=input_layer,
                                                   logits=logits)
    cost = tf.reduce_mean(loss, name='cost')
    optimizer = tf.train.AdamOptimizer(learning_rate)
    train = optimizer.minimize(cost, name='train')    

    # Saver to save session for reuse
    saver = tf.train.Saver()


# In[3]:


import numpy as np

##########################
### TRAINING & EVALUATION
##########################
    
with tf.Session(graph=g) as sess:
    sess.run(tf.global_variables_initializer())

    np.random.seed(random_seed) # random seed for mnist iterator
    for epoch in range(training_epochs):
        avg_cost = 0.
        total_batch = mnist.train.num_examples // batch_size

        for i in range(total_batch):
            batch_x, batch_y = mnist.train.next_batch(batch_size)
            _, c = sess.run(['train', 'cost:0'], feed_dict={'input:0': batch_x})
            avg_cost += c

            if not i % print_interval:
                print("Minibatch: %03d | Cost:    %.3f" % (i + 1, c))

        print("Epoch:     %03d | AvgCost: %.3f" % (epoch + 1, avg_cost / (i + 1)))
    
    saver.save(sess, save_path='./autoencoder.ckpt')


# In[5]:


import matplotlib.pyplot as plt

##########################
### VISUALIZATION
##########################

n_images = 15

fig, axes = plt.subplots(nrows=2, ncols=n_images, sharex=True, 
                         sharey=True, figsize=(20, 2.5))
test_images = mnist.test.images[:n_images]

with tf.Session(graph=g) as sess:
    saver.restore(sess, save_path='./autoencoder.ckpt')
    decoded = sess.run('decoding:0', feed_dict={'input:0': test_images})

    input_graph_def = tf.get_default_graph().as_graph_def()
    output_graph_def = tf.graph_util.convert_variables_to_constants(
        sess,  # The session
        input_graph_def,  # input_graph_def is useful for retrieving the nodes
        "decoding".split(",")
    )
with tf.gfile.FastGFile('./ae-conv.pb', "wb") as f:
    f.write(output_graph_def.SerializeToString())

for i in range(n_images):
    for ax, img in zip(axes, [test_images, decoded]):
        ax[i].imshow(img[i].reshape((image_width, image_width)), cmap='binary')

plt.savefig("result_ae-conv.png")
"""
source activate TFlite
tflite_convert \
--graph_def_file=/home/chen/Documents/deeplearning-models-master/tensorflow1_ipynb/autoencoder/ae-conv.pb \
--output_file=/home/chen/Documents/deeplearning-models-master/tensorflow1_ipynb/autoencoder/ae-conv.lite \
--output_format=TFLITE \
--input_shapes=15,784 \
--input_arrays=input \
--output_arrays=decoding \
--inference_type=FLOAT
"""