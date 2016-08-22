import numpy as np
from functools import reduce
#import time

def YUV(image):
    return np.uint8(image[:,:,:1] * 0.299 + image[:,:,1:2] * 0.587 + image[:,:,2:] * 0.114).reshape(image.shape[:2])

def Energy(yuv_image):
    yuv_image = np.int32(yuv_image)
    x = np.empty((yuv_image.shape[:2]), dtype=np.int32)
    y = np.empty((yuv_image.shape[:2]), dtype=np.int32)
    x[:,:1] = yuv_image[:,1:2] - yuv_image[:,:1]
    x[:,1:-1] = yuv_image[:,2:] - yuv_image[:,:-2]
    x[:,-1:] = yuv_image[:,-1:] - yuv_image[:,-2:-1]
    y[:1,:] = yuv_image[1:2,:] - yuv_image[:1,:]
    y[1:-1,:] = yuv_image[2:,:] - yuv_image[:-2,:]
    y[-1:,:] = yuv_image[-1:,:] - yuv_image[-2:-1,:]
    return np.uint8((x ** 2 + y ** 2) ** 0.5)
    
def Find_min_index(h, w, image):
    if w == 0:
        if image[h][w] <= image[h][w + 1]:
            return w
        else:
            return w + 1
    elif w == image.shape[1] - 1:
        if image[h][w - 1] <= image[h][w]:
            return w - 1
        else:
            return w
    else:
        if image[h][w - 1] <= image[h][w] and image[h][w - 1] <= image[h][w + 1]:
            return w - 1
        elif image[h][w] <= image[h][w + 1]:
            return w
        else:
            return w + 1

def Find_seam(image, mode, mask):
    #start = time.time()
    yuv = YUV(image)
    energy_image = Energy(yuv)
    energy_image = np.int64(energy_image)
    
    if mask is not None:
        mask = np.int64(mask)
        energy_image += mask * mask.size * 256
    height = image.shape[0]
    width = image.shape[1]
    if 'vertical' in mode:
        height, width = width, height
        energy_image = energy_image.transpose()
    matrix = np.int64(np.zeros((height, width)))
    matrix[0] = energy_image[0]
    #print('find seam befor for -', time.time() - start)
    for h in range(1, height):
        matrix[h][0] = min(matrix[h - 1][0], matrix[h - 1][1]) + energy_image[h][0]
        matrix[h][1:-1] = np.minimum.reduce([matrix[h - 1][0:-2],
                                             matrix[h - 1][1:-1],
                                             matrix[h - 1][2:]]) + energy_image[h][1:-1]
        matrix[h][-1] = min(matrix[h - 1][-2], matrix[h - 1][-1]) + energy_image[h][-1]
        #for w in range(width):
            #matrix[h][w] = int(Find_min_cell(h - 1, w, matrix)) + energy_image[h][w]
    #print('find seam after for -', time.time() - start)
    min_cell = matrix[height - 1][width - 1]
    min_index = width - 1
    for w in range(width - 1, -1, -1):
        if matrix[height - 1][w] <= min_cell:
            min_cell = matrix[height - 1][w]
            min_index = w
    print(min_index)
    #print('find seam after cell -', time.time() - start)
    min_cells = [min_index]
    for h in range(height - 1, 0, -1):
        min_index = Find_min_index(h - 1, min_index, matrix)
        min_cells.append(min_index)
    #print('find seam -', time.time() - start)
    return min_cells

def seam_carve(image, mode, mask=None):
    #start = time.time()
    if mask is None:
        min_seam = Find_seam(image, mode, mask)
        height = image.shape[0]
        width = image.shape[1]
        if 'vertical' in mode:
            height, width = width, height
            image = image.transpose(1, 0, 2)
        if 'shrink' in mode:
            new_image = np.empty((height, width - 1, 3))
        else:
            new_image = np.empty((height, width + 1, 3))
        carve_mask = np.zeros((height, width))  #danger with types!!!
        for h in range(height - 1, -1, -1):
            if 'shrink' in mode:
                new_image[h] = np.delete(image[h], min_seam[height - h - 1], 0)
            else:
                if 0 in min_seam:
                    mid = np.uint8((np.int16(image[h][min_seam[height - h - 1]])
                             + np.int16(image[h][min_seam[height - h - 1] + 1])) // 2)
                else:
                    mid = np.uint8((np.int16(image[h][min_seam[height - h - 1]])
                             + np.int16(image[h][min_seam[height - h - 1] - 1])) // 2)
                new_image[h] = np.insert(image[h], min_seam[height - h - 1], mid, 0)
            carve_mask[h][min_seam[height - h - 1]] = 1
        if 'vertical' in mode:
            new_image = new_image.transpose(1, 0, 2)
            carve_mask = carve_mask.transpose()
        #print('find seam -', time.time() - start)
        return (np.uint8(new_image), None, carve_mask)
    else:
        min_seam = Find_seam(image, mode, mask)
        height = image.shape[0]
        width = image.shape[1]
        if 'vertical' in mode:
            height, width = width, height
            image = image.transpose(1, 0, 2)
            mask = mask.transpose()
        if 'shrink' in mode:
            new_image = np.empty((height, width - 1, 3))
            new_mask = np.empty((height, width - 1))
        else:
            new_image = np.empty((height, width + 1, 3))
            new_mask = np.empty((height, width + 1))
        carve_mask = np.zeros((height, width))  #danger with types!!!
        for h in range(height - 1, -1, -1):
            if 'shrink' in mode:
                new_image[h] = np.delete(image[h], min_seam[height - h - 1], 0)
                new_mask[h] = np.delete(mask[h], min_seam[height - h - 1], 0)
            else:
                if 0 in min_seam:
                    mid = np.uint8((np.int16(image[h][min_seam[height - h - 1]])
                             + np.int16(image[h][min_seam[height - h - 1] + 1])) // 2)
                    right_seam = True
                else:
                    mid = np.uint8((np.int16(image[h][min_seam[height - h - 1]])
                             + np.int16(image[h][min_seam[height - h - 1] - 1])) // 2)
                    right_seam = False
                new_image[h] = np.insert(image[h], min_seam[height - h - 1], mid, 0)
                new_mask[h] = np.insert(mask[h], min_seam[height - h - 1], 1, 0)#здесb новый шов:
                new_mask[h][min_seam[height - h - 1] + 1] = 1
                new_mask[h][min_seam[height - h - 1] - 1] = 1
            #print(new_mask[h].sum())
            carve_mask[h][min_seam[height - h - 1]] = 1
        if 'vertical' in mode:
            new_image = new_image.transpose(1, 0, 2)
            new_mask = new_mask.transpose()
            carve_mask = carve_mask.transpose()
        #print('find seam -', time.time() - start)
        return (np.uint8(new_image), new_mask, carve_mask)
