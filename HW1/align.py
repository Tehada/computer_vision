import numpy as np
from skimage.transform import resize
from skimage import img_as_ubyte

SHIFT = 18

def Crop_percents(image, percentage):
    height = image.shape[0]
    crop_height = height * percentage // 100
    width = image.shape[1]
    crop_length = width * percentage // 100
    image = image[crop_height:height - crop_height,
                  crop_length:width - crop_length]
    return image

def Crop_pixels(image, left, down, right, up):
    if right < 0:
        right *= -1
        image = image[:, right:]
    else:
        image = image[:, :image.shape[1] - right]
    if left < 0:
        left *= -1
        image = image[:, :image.shape[1] - left]
    else:
        image = image[:, left:]
    if up < 0:
        up *= -1
        image = image[:image.shape[0] - up, :]
    else:
        image = image[up:, :]
    if down < 0:
        down *= -1
        image = image[down:, :]
    else:
        image = image[:image.shape[0] - down, :]
    return image

def Divide(image):
    height = image.shape[0] // 3
    red_channel = image[:height, :]
    green_channel = image[height:height * 2, :]
    blue_channel = image[height * 2:height * 3, :]
    return [red_channel, green_channel, blue_channel]

def MSE(image_1, image_2):
    return ((np.int16(image_1) - np.int16(image_2)) ** 2).sum() / (image_1.shape[0] * image_1.shape[1])

def CC(image_1, image_2):
    image_1 = np.float64(image_1)
    image_2 = np.float64(image_2)
    return round((image_1 * image_2).sum() /
                 (image_1.sum() * image_2.sum()) * image_1.shape[0] * image_1.shape[1], 4)

def MSE_overlay(image_1, image_2, shift):
    min_metric = MSE(image_1, image_2)
    shift_x = 0
    shift_y = 0
    for y in range(-shift, shift + 1):
        for x in range(-shift, shift + 1):
            temp_metric = MSE(Crop_pixels(image_1, x, y, 0, 0), Crop_pixels(image_2, 0, 0, x, y))
            if temp_metric < min_metric:
                min_metric = temp_metric
                shift_x = x
                shift_y = y
    return [shift_x, shift_y]

def CC_overlay(image_1, image_2, shift):
    max_metric = CC(image_1, image_2)
    shift_x = 0
    shift_y = 0
    for y in range(-shift, shift + 1):
        for x in range(-shift, shift + 1):
            temp_metric = CC(Crop_pixels(image_1, x, y, 0, 0), Crop_pixels(image_2, 0, 0, x, y))
            if temp_metric - max_metric > 0.0005:
                max_metric = temp_metric
                shift_x = x
                shift_y = y
    return [shift_x, shift_y]

def Find_rgb_crops(red, green, blue, shift, metric):
    if metric == 'mse':
        rg = MSE_overlay(red, green, shift)
        rb = MSE_overlay(red, blue, shift)
    elif metric == 'cc':
        rg = CC_overlay(red, green, shift)
        rb = CC_overlay(red, blue, shift)
    height = red.shape[0]
    width = red.shape[1]
    red_corners = [[0, 0], [width - 1, 1 - height]]
    green_corners = [[rg[0], rg[1]], [rg[0] + width - 1, rg[1] + 1 - height]]
    blue_corners = [[rb[0], rb[1]], [rb[0] + width - 1, rb[1] + 1 - height]]
    final_corners = [[max(red_corners[0][0], max(green_corners[0][0], blue_corners[0][0])),
           min(red_corners[0][1], min(green_corners[0][1], blue_corners[0][1]))],
          [min(red_corners[1][0], min(green_corners[1][0], blue_corners[1][0])),
           max(red_corners[1][1], max(green_corners[1][1], blue_corners[1][1]))]]
    
    red_frame = [final_corners[0][0], height + final_corners[1][1] - 1,
                width - final_corners[1][0] - 1, -final_corners[0][1]]

    green_frame = [final_corners[0][0] - rg[0], height + (final_corners[1][1] - rg[1]) - 1,
                  width - (final_corners[1][0] - rg[0]) - 1, -(final_corners[0][1] - rg[1])]

    blue_frame = [final_corners[0][0] - rb[0], height + (final_corners[1][1] - rb[1]) - 1,
                 width - (final_corners[1][0] - rb[0]) - 1, -(final_corners[0][1] - rb[1])]
    return [red_frame, green_frame, blue_frame]

def Pyramid(red, green, blue, metric):
    if red.shape[0] < 500:
        return Find_rgb_crops(red, green, blue, SHIFT, metric)
    new_size = red.shape[0] // 2
    t_red = resize(red, (new_size, int(red.shape[1] * new_size / red.shape[0])), preserve_range=True)
    t_green = resize(green, (new_size, int(green.shape[1] * new_size / green.shape[0])), preserve_range=True)
    t_blue = resize(blue, (new_size, int(blue.shape[1] * new_size / blue.shape[0])), preserve_range=True)
    crops_1 = Pyramid(t_red, t_green, t_blue, metric)
    for i in range(3):
        for j in range(4):
            crops_1[i][j] *= 2
    t_red = Crop_pixels(red, crops_1[0][0], crops_1[0][1], crops_1[0][2], crops_1[0][3])
    t_green = Crop_pixels(green, crops_1[1][0], crops_1[1][1], crops_1[1][2], crops_1[1][3])
    t_blue = Crop_pixels(blue, crops_1[2][0], crops_1[2][1], crops_1[2][2], crops_1[2][3])
    crops_2 = Find_rgb_crops(t_red, t_green, t_blue, 1, metric)
    crops = [[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]
    for i in range(3):
        for j in range(4):
            crops[i][j] = crops_1[i][j] + crops_2[i][j]
    return crops

def align(bgr_image, metric = 'cc'):
    bgr_image = img_as_ubyte(bgr_image)
    channels = Divide(bgr_image)
    for i in range(3):
        channels[i] = Crop_percents(channels[i], 5)
    crops = Pyramid(channels[0], channels[1], channels[2], metric)
    red = Crop_pixels(channels[0], crops[0][0], crops[0][1], crops[0][2], crops[0][3])
    green = Crop_pixels(channels[1], crops[1][0], crops[1][1], crops[1][2], crops[1][3])
    blue = Crop_pixels(channels[2], crops[2][0], crops[2][1], crops[2][2], crops[2][3])
    bgr_image = np.dstack((blue, green, red))
    return bgr_image
