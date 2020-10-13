# -*- coding: utf-8 -*-
import cv2
import numpy as np

def recognition_table_from_image_file(filename, area_range):
    cv2_image = cv2.imread( str(filename) )

    gray = cv2.cvtColor(cv2_image, cv2.COLOR_BGR2GRAY)
    edge = cv2.Canny(gray, 1, 100, apertureSize=3)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    edge = cv2.dilate(edge, kernel)

    contours, hierarchy = cv2.findContours(edge, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    approxes = []
    for contour, hierarchy in zip(contours, hierarchy[0]):

        area = cv2.contourArea(contour)
        if not area_range[0] < area < area_range[1]:
            continue

        approx = cv2.approxPolyDP(contour, 0.01*cv2.arcLength(contour, True), True)
        if len(approx) == 4:
            approxes.append(approx)
    
    approxes = sorted( approxes, key=lambda x: (x.ravel()[1], x.ravel()[0]) )

    rects, crops, crop_images = [], [], []
    for approx in approxes:

        p1, p3 = approx[0][0], approx[2][0]
        x, y = p1[0], p1[1]
        w, h = p3[0] - p1[0], p3[1] - p1[1]
        rect =  [x, y, w, h]

        if same_rect_is_in_rects(rect, rects, 10):
            continue
        if h < 1 or w < 1:
            continue
        rects.append(rect)
        crop_image = cv2_image[y:y+h, x:x+w]
        crop_image, crop = crop_margin(crop_image)
        crop = [x + crop[0], y + crop[1], crop[2], crop[3]]
        crop_images.append(crop)
        crops.append(crop)

    data = {}
    data['cv2_image'] = cv2_image
    data['edge'] = edge
    data['rects'] = rects
    data['crops'] = crops

    return data

def same_rect_is_in_rects(rect1, rects, tolerance=5):
    for rect2 in rects:
        frag = True
        for r1, r2 in zip(rect1, rect2):
            if not r2 - tolerance < r1 < r2 + tolerance:
                frag = False
                break
        if frag:
            return True
    return False

def crop_margin(cv2_image):
    img = cv2_image

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    img2 = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)[1]
    contours = cv2.findContours(img2, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)[0]
    
    x1, y1, x2, y2 = [], [], [], []
    for i in range(1, len(contours)):
        ret = cv2.boundingRect(contours[i])
        x1.append(ret[0])
        y1.append(ret[1])
        x2.append(ret[0] + ret[2])
        y2.append(ret[1] + ret[3])

    x1_min, y1_min, x2_max, y2_max = min(x1), min(y1), max(x2), max(y2)
    crop_img = img2[y1_min:y2_max, x1_min:x2_max]
    crop = [x1_min, y1_min, x2_max - x1_min, y2_max - y1_min]

    return crop_img, crop
