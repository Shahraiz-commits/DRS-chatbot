import tensorflow as tf
from tensorflow.python.client import device_lib
print(device_lib.list_local_devices())
print("Num GPUs Available: ", len(tf.config.list_physical_devices('GPU')))
print(tf.test.is_built_with_cuda()) # Only 2.10 has cuda support on windows native. Other option is to switch to WSL2
print(tf.config.list_physical_devices('GPU'))