"""Utility functions for preprocessing data sets."""

from PIL import Image
import numpy as np
import tensorflow as tf

_R_MEAN = 123.68
_G_MEAN = 116.78
_B_MEAN = 103.94




def mean_image_addition(image, means=(_R_MEAN, _G_MEAN, _B_MEAN)):
  """Adds the given means from each image channel.

  For example:
    means = [123.68, 116.779, 103.939]
    image = _mean_image_subtraction(image, means)

  Note that the rank of `image` must be known.

  Args:
    image: a tensor of size [height, width, C].
    means: a C-vector of values to subtract from each channel.

  Returns:
    the centered image.

  Raises:
    ValueError: If the rank of `image` is unknown, if `image` has a rank other
      than three or if the number of channels in `image` doesn't match the
      number of values in `means`.
  """
  if image.get_shape().ndims != 3:
    raise ValueError('Input must be of size [height, width, C>0]')
  num_channels = image.get_shape().as_list()[-1]
  if len(means) != num_channels:
    raise ValueError('len(means) must match the number of channels')

  channels = tf.split(axis=2, num_or_size_splits=num_channels, value=image)
  for i in range(num_channels):
    channels[i] += means[i]
  return tf.concat(axis=2, values=channels)


def mean_image_subtraction(image, means=(_R_MEAN, _G_MEAN, _B_MEAN)):
  """Subtracts the given means from each image channel.

  For example:
    means = [123.68, 116.779, 103.939]
    image = _mean_image_subtraction(image, means)

  Note that the rank of `image` must be known.

  Args:
    image: a tensor of size [height, width, C].
    means: a C-vector of values to subtract from each channel.

  Returns:
    the centered image.

  Raises:
    ValueError: If the rank of `image` is unknown, if `image` has a rank other
      than three or if the number of channels in `image` doesn't match the
      number of values in `means`.
  """
  if image.get_shape().ndims != 3:
    raise ValueError('Input must be of size [height, width, C>0]')
  num_channels = image.get_shape().as_list()[-1]
  if len(means) != num_channels:
    raise ValueError('len(means) must match the number of channels')

  channels = tf.split(axis=2, num_or_size_splits=num_channels, value=image)
  for i in range(num_channels):
    channels[i] -= means[i]
  return tf.concat(axis=2, values=channels)


def random_rescale_image_and_label(image, label, min_scale, max_scale):
  """Rescale an image and label with in target scale.

  Rescales an image and label within the range of target scale.

  Args:
    image: 3-D Tensor of shape `[height, width, channels]`.
    label: 3-D Tensor of shape `[height, width, 1]`.
    min_scale: Min target scale.
    max_scale: Max target scale.

  Returns:
    Cropped and/or padded image.
    If `images` was 3-D, a 3-D float Tensor of shape
    `[new_height, new_width, channels]`.
    If `labels` was 3-D, a 3-D float Tensor of shape
    `[new_height, new_width, 1]`.
  """
  if min_scale <= 0:
    raise ValueError('\'min_scale\' must be greater than 0.')
  elif max_scale <= 0:
    raise ValueError('\'max_scale\' must be greater than 0.')
  elif min_scale >= max_scale:
    raise ValueError('\'max_scale\' must be greater than \'min_scale\'.')

  shape = tf.shape(image)
  height = tf.to_float(shape[0])
  width = tf.to_float(shape[1])
  scale = tf.random_uniform(
      [], minval=min_scale, maxval=max_scale, dtype=tf.float32)
  new_height = tf.to_int32(height * scale)
  new_width = tf.to_int32(width * scale)
  image = tf.image.resize_images(image, [new_height, new_width],
                                 method=tf.image.ResizeMethod.BILINEAR)
  # Since label classes are integers, nearest neighbor need to be used.
  label = tf.image.resize_images(label, [new_height, new_width],
                                 method=tf.image.ResizeMethod.NEAREST_NEIGHBOR)

  return image, label


def random_crop_or_pad_image_and_label(image, label, crop_height, crop_width, ignore_label):
  """Crops and/or pads an image to a target width and height.

  Resizes an image to a target width and height by rondomly
  cropping the image or padding it evenly with zeros.

  Args:
    image: 3-D Tensor of shape `[height, width, channels]`.
    label: 3-D Tensor of shape `[height, width, 1]`.
    crop_height: The new height.
    crop_width: The new width.
    ignore_label: Label class to be ignored.

  Returns:
    Cropped and/or padded image.
    If `images` was 3-D, a 3-D float Tensor of shape
    `[new_height, new_width, channels]`.
  """
  label = label - ignore_label  # Subtract due to 0 padding.
  label = tf.to_float(label)
  image_height = tf.shape(image)[0]
  image_width = tf.shape(image)[1]
  image_and_label = tf.concat([image, label], axis=2)
  image_and_label_pad = tf.image.pad_to_bounding_box(
      image_and_label, 0, 0,
      tf.maximum(crop_height, image_height),
      tf.maximum(crop_width, image_width))
  image_and_label_crop = tf.random_crop(
      image_and_label_pad, [crop_height, crop_width, 4])

  image_crop = image_and_label_crop[:, :, :3]
  label_crop = image_and_label_crop[:, :, 3:]
  label_crop += ignore_label
  label_crop = tf.to_int32(label_crop)

  return image_crop, label_crop


def random_flip_left_right_image_and_label(image, label):
  """Randomly flip an image and label horizontally (left to right).

  Args:
    image: A 3-D tensor of shape `[height, width, channels].`
    label: A 3-D tensor of shape `[height, width, 1].`

  Returns:
    A 3-D tensor of the same type and shape as `image`.
    A 3-D tensor of the same type and shape as `label`.
  """
  uniform_random = tf.random_uniform([], 0, 1.0)
  mirror_cond = tf.less(uniform_random, .5)
  image = tf.cond(mirror_cond, lambda: tf.reverse(image, [1]), lambda: image)
  label = tf.cond(mirror_cond, lambda: tf.reverse(label, [1]), lambda: label)

  return image, label