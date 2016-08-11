%matplotlib inline
from numpy import array, dstack, roll
from skimage.transform import rescale, resize

SHIFT = 15
COUNT = 0

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
#    print('we are in MSE')
    height = image_1.shape[0]
    width = image_1.shape[1]
    total = 0
    for y in range(height):
        for x in range(width):
            value = (float(image_1[y][x]) - float(image_2[y][x])) ** 2
            total += value
    return total / (width * height)

def CC(image_1, image_2):
    height = image_1.shape[0]
    width = image_1.shape[1]
    sum_1 = 0
    sum_2 = 0
    sum_3 = 0
    for y in range(height):
        for x in range(width):
            sum_1 += int(image_1[y][x]) * int(image_2[y][x])
            sum_2 += int(image_1[y][x])
            sum_3 += int(image_2[y][x])
    return sum_1 / (sum_2 * sum_3)

def MSE_overlay(image_1, image_2, shift):
    print('we are in MSE overlay')
    min_metric = MSE(image_1, image_2)
    shift_x = 0
    shift_y = 0
    for y in range(-shift, shift + 1):
        for x in range(-shift, shift + 1):
            temp_metric = MSE(Crop_pixels(image_1, x, y, 0, 0), Crop_pixels(image_2, 0, 0, x, y))
#            print('temp_metric =', temp_metric)
            if temp_metric < min_metric:
                min_metric = temp_metric
                shift_x = x
                shift_y = y
                print('min_metric =', int(min_metric))
    print('finish')
    return [shift_x, shift_y]

def CC_overlay(image_1, image_2, shift):
    max_metric = CC(image_1, image_2)
    shift_x = 0
    shift_y = 0
    for y in range(-shift, shift + 1):
        for x in range(-shift, shift + 1):
            temp_metric = CC(Crop_pixels(image_1, x, y, 0, 0), Crop_pixels(image_2, 0, 0, x, y))
#            print('temp_metric =', temp_metric)
            if temp_metric > max_metric:
                max_metric = temp_metric
                shift_x = x
                shift_y = y
                print('max_metric =', max_metric)
    print('finish')
    return [shift_x, shift_y]

def Find_rgb_crops(red, green, blue, shift):
    rg = MSE_overlay(red, green, shift)
    rb = MSE_overlay(red, blue, shift)
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

def Crop_pixels_2(red, green, blue, red_crops, green_crops, blue_crops):
    return [Crop_pixels(red, red_crops[0], red_crops[1],
                             red_crops[2], red_crops[3]),
            Crop_pixels(green, green_crops[0],
                                   green_crops[1],
                                   green_crops[2],
                                   green_crops[3]),
            Crop_pixels(blue, blue_crops[0],
                                  blue_crops[1],
                                  blue_crops[2],
                                  blue_crops[3])]

def Pyramid(red, green, blue, count):
    count += 1
    print(count)
    if red.shape[0] < 500:
        return Find_rgb_crops(red, green, blue, SHIFT)

#Уменьшение изображений вдвое
    new_size = red.shape[0] // 2
    t_red = resize(red, (new_size, int(red.shape[1] * new_size / red.shape[0])))
    t_green = resize(green, (new_size, int(green.shape[1] * new_size / green.shape[0])))
    t_blue = resize(blue, (new_size, int(blue.shape[1] * new_size / blue.shape[0])))
    
#Запуск рекурсии
    crops_1 = Pyramid(t_red, t_green, t_blue, count)
    
#Промежуточное объединение каналов
    n_red = Crop_pixels(t_red, crops_1[0][0], crops_1[0][1], crops_1[0][2], crops_1[0][3])
    n_green = Crop_pixels(t_green, crops_1[1][0], crops_1[1][1], crops_1[1][2], crops_1[1][3])
    n_blue = Crop_pixels(t_blue, crops_1[2][0], crops_1[2][1], crops_1[2][2], crops_1[2][3])
    image = dstack((n_blue, n_green, n_red))
#    io.imsave('/home/tehada/cvintro2016/hw-01/egg_python/photo' + str(count) + '.png', image)
    
#Удвоение обрезков для исходной картинки
    for channel in crops_1:
        for frame in channel:
            frame *= 2

#Создание временных изображения для сдвига на 1 пиксель
    t_red = Crop_pixels(red, crops_1[0][0], crops_1[0][1], crops_1[0][2], crops_1[0][3])
    t_green = Crop_pixels(green, crops_1[1][0], crops_1[1][1], crops_1[1][2], crops_1[1][3])
    t_blue = Crop_pixels(blue, crops_1[2][0], crops_1[2][1], crops_1[2][2], crops_1[2][3])
    crops_2 = Find_rgb_crops(t_red, t_green, t_blue, 1)
    t_crops = [0, 0, 0, 0]
    crops = []
    
#Сложение полученных обрезков
    for i in range(3):
        for j in range(4):
            t_crops[j] = crops_1[i][j] + crops_2[i][j]
        crops.append(t_crops)
    return crops

def align(bgr_image):
    channels = Divide(bgr_image)
    for i in range(3):
        channels[i] = Crop_percents(channels[i], 5)
        io.imsave('/home/tehada/cvintro2016/hw-01/egg_python/divimg' + str(i) + '.png', channels[i])
    print('hi!')
    count = 0
    h = channels[0].shape[0] // 8
    l = channels[0].shape[1] // 8

#    print('MSE rg1 =', MSE(channels[0], channels[1]))
#    print(channels[0], '\n----\n', channels[1], '\n--------\n')
    
    channels[0] = resize(channels[0], (297, 359))
    channels[1] = resize(channels[1], (297, 359))
    channels[2] = resize(channels[2], (297, 359))
    
#    print('MSE rg2 =', MSE(channels[0], channels[1]))
#    print(channels[0], '\n----\n', channels[1])
    
    crops = Pyramid(channels[0], channels[1], channels[2], count)
    red = Crop_pixels(channels[0], crops[0][0], crops[0][1], crops[0][2], crops[0][3])
    green = Crop_pixels(channels[1], crops[1][0], crops[1][1], crops[1][2], crops[1][3])
    blue = Crop_pixels(channels[2], crops[2][0], crops[2][1], crops[2][2], crops[2][3])
#    io.imsave('/home/tehada/cvintro2016/hw-01/egg_python/2red1.png', red)
#    io.imsave('/home/tehada/cvintro2016/hw-01/egg_python/2green1.png', green)
#    io.imsave('/home/tehada/cvintro2016/hw-01/egg_python/2blue1.png', blue)
    bgr_image = dstack((blue, green, red))
    return bgr_image