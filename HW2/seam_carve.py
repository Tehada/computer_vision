import numpy as np
from functools import reduce

def YUV(image):
    return np.float64(image[:,:,:1] * 0.299 + image[:,:,1:2] * 0.587 + image[:,:,2:] * 0.114).reshape(image.shape[:2])

def Energy(yuv_image):
    yuv_image = np.float64(yuv_image)
    x = np.empty((yuv_image.shape[:2]), dtype=np.float64)
    y = np.empty((yuv_image.shape[:2]), dtype=np.float64)
    x[:,:1] = yuv_image[:,1:2] - yuv_image[:,:1]
    x[:,1:-1] = yuv_image[:,2:] - yuv_image[:,:-2]
    x[:,-1:] = yuv_image[:,-1:] - yuv_image[:,-2:-1]
    y[:1,:] = yuv_image[1:2,:] - yuv_image[:1,:]
    y[1:-1,:] = yuv_image[2:,:] - yuv_image[:-2,:]
    y[-1:,:] = yuv_image[-1:,:] - yuv_image[-2:-1,:]
    return np.float64((x ** 2 + y ** 2) ** 0.5)
 
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
    yuv = YUV(image)
    energy_image = Energy(yuv)
    energy_image = np.float64(energy_image)
    if mask is not None:
        mask = np.int64(mask)
        energy_image += mask * mask.size * 256
    height = image.shape[0]
    width = image.shape[1]
    if 'vertical' in mode:
        height, width = width, height
        energy_image = energy_image.transpose()
    matrix = np.float64(np.zeros((height, width)))
    matrix[0] = energy_image[0]
    for h in range(1, height):
        matrix[h][0] = min(matrix[h - 1][0], matrix[h - 1][1]) + energy_image[h][0]
        matrix[h][1:-1] = np.minimum.reduce([matrix[h - 1][0:-2],
                                             matrix[h - 1][1:-1],
                                             matrix[h - 1][2:]]) + energy_image[h][1:-1]
        matrix[h][-1] = min(matrix[h - 1][-2], matrix[h - 1][-1]) + energy_image[h][-1]
    min_index = np.argmin(matrix[-1])
    min_cell = matrix[-1][min_index]
    min_cells = [min_index]
    for h in range(height - 1, 0, -1):
        min_index = Find_min_index(h - 1, min_index, matrix)
        min_cells.append(min_index)
    return min_cells

def seam_carve(image, mode, mask=None):
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
        carve_mask = np.zeros((height, width))
        for h in range(height - 1, -1, -1):
            if 'shrink' in mode:
                new_image[h] = np.delete(image[h], min_seam[height - h - 1], 0)
            else:
                if width - 1 in min_seam:
                    mid = np.uint8((np.int16(image[h][min_seam[height - h - 1]])
                             + np.int16(image[h][min_seam[height - h - 1] - 1])) // 2)
                else:
                    mid = np.uint8((np.int16(image[h][min_seam[height - h - 1]])
                             + np.int16(image[h][min_seam[height - h - 1] + 1])) // 2)
                new_image[h] = np.insert(image[h], min_seam[height - h - 1], mid, 0)
            carve_mask[h][min_seam[height - h - 1]] = 1
        if 'vertical' in mode:
            new_image = new_image.transpose(1, 0, 2)
            carve_mask = carve_mask.transpose()
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
        carve_mask = np.zeros((height, width))
        for h in range(height - 1, -1, -1):
            if 'shrink' in mode:
                new_image[h] = np.delete(image[h], min_seam[height - h - 1], 0)
                new_mask[h] = np.delete(mask[h], min_seam[height - h - 1], 0)
            else:
                if width - 1 in min_seam:
                    mid = np.uint8((np.int16(image[h][min_seam[height - h - 1]])
                             + np.int16(image[h][min_seam[height - h - 1] - 1])) // 2)
                else:
                    mid = np.uint8((np.int16(image[h][min_seam[height - h - 1]])
                             + np.int16(image[h][min_seam[height - h - 1] + 1])) // 2)
                new_image[h] = np.insert(image[h], min_seam[height - h - 1], mid, 0)
                new_mask[h] = np.insert(mask[h], min_seam[height - h - 1], 1, 0)
                new_mask[h][min_seam[height - h - 1] + 1] = 1
                new_mask[h][min_seam[height - h - 1] - 1] = 1
            carve_mask[h][min_seam[height - h - 1]] = 1
        if 'vertical' in mode:
            new_image = new_image.transpose(1, 0, 2)
            new_mask = new_mask.transpose()
            carve_mask = carve_mask.transpose()
        return (np.uint8(new_image), new_mask, carve_mask)
