# -*- coding: utf-8 -*-
import cv2
import numpy as np

def recognition_table_from_image_file(filename, area_range):
    cv2_image = cv2.imread(str(filename))

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

    rects = []
    for approx in approxes:
        p1, p3 = approx[0][0], approx[2][0]
        x, y = p1[0], p1[1]
        w, h = p3[0] - p1[0], p3[1] - p1[1]
        rect =  [x, y, w, h]
        if not same_rect_is_in_rects(rect, rects, 10):
            rects.append(rect)

    rgb_image = cv2.cvtColor(cv2_image, cv2.COLOR_BGR2RGB)

    data = {}
    data['cv2_image'] = cv2_image
    data['rgb_image'] = rgb_image
    data['approxes'] = approxes
    data['edge'] = edge
    data['rects'] = rects

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