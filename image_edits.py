import math
import time

import cv2
import numpy as np
import image_detectations as detects

num_size = 0
percent = 2
resized = None
elements = None


def read(fname):
    # Beolvasás
    global img, img_orig
    img_orig = cv2.imread(fname, cv2.IMREAD_GRAYSCALE)

    #img_orig = cv2.imread('Inputs/chart_xbar.png', cv2.IMREAD_GRAYSCALE)
    # img_orig = cv2.imread('Inputs/xbar_str.png', cv2.IMREAD_GRAYSCALE)
    # img_orig = cv2.imread('Inputs/ybar_str.png', cv2.IMREAD_GRAYSCALE)
    # img_orig = cv2.imread('Inputs/chart_xbar_str.png', cv2.IMREAD_GRAYSCALE)

    # img_orig = cv2.imread('Inputs/chart_ybar.png', cv2.IMREAD_GRAYSCALE)
    # img_orig = cv2.imread('Inputs/chart_ybar_r.png', cv2.IMREAD_GRAYSCALE)

    # img_orig = cv2.imread('Inputs/chart_xbar_ex.png', cv2.IMREAD_GRAYSCALE)

    # img_orig = cv2.imread('Inputs/chart_longtitle.png', cv2.IMREAD_GRAYSCALE)
    # img_orig = cv2.imread('Inputs/chart_stacked.png', cv2.IMREAD_GRAYSCALE)
    # img_orig = cv2.imread('Inputs/chart_title.png', cv2.IMREAD_GRAYSCALE)

    # img_orig = cv2.imread('Inputs/chart_ybar_ex.png', cv2.IMREAD_GRAYSCALE)
    # img_orig = cv2.imread('Inputs/xbar_rotate_l.png', cv2.IMREAD_GRAYSCALE)
    # img_orig = cv2.imread('Inputs/xbar_rotate_r.png', cv2.IMREAD_GRAYSCALE)
    img = img_orig.copy()
    # cv2.imshow('chart', img)
    return img

def upscale():
    # Felskálázás
    global img, num_size, resized, percent
    # cv2.imshow("img", img)
    width = int(img.shape[1] * percent)
    height = int(img.shape[0] * percent)
    img = cv2.resize(img, (width, height))
    num_size = img.shape[0] * img.shape[1] / 1000
    # print(img.shape[0]*img.shape[1])
    # print('num_size: ', num_size)
    resized = img.copy()
    # cv2.imshow('resized', resized)

def treshold():
    # Küszöbölés
    global img
    k = -1
    block_size = 5
    img = cv2.ximgproc.niBlackThreshold(img, 255, cv2.THRESH_TRUNC, block_size, k, binarizationMethod=0, r=108)
    # cv2.imshow('nib', img)
    # cv2.imwrite('nib.png', img)


def create_binary():
    # Bináris létrehozása
    global binary, hugh
    binary = np.ndarray(img.shape)
    binary.fill(0)
    binary[img < 200] = 255
    binary = np.uint8(binary)
    # cv2.imshow('binary', binary)
    # cv2.imwrite('binary_xbar.png', binary)
    hugh = cv2.Canny(img, 50, 200, None, 3)
    # cv2.imshow('binary', binary)
    # cv2.imshow('hugh', hugh)
    return binary


def rotate():
    global binary, percent, img_orig, hugh, resized, img

    cdst = cv2.cvtColor(hugh, cv2.COLOR_GRAY2BGR)

    lines = None
    expectation = 200 * percent
    while lines is None or len(lines) < 10:
        lines = cv2.HoughLines(hugh, 1, np.pi / 50, expectation, None, 0, 0)
        expectation = expectation - 5

    # lines = cv2.HoughLines(hugh, 1, np.pi/180, 300, None, 0, 0)
    sizemax = math.sqrt(cdst.shape[0] ** 2 + cdst.shape[1] ** 2)
    all_deg = 0

    if lines is not None:
        # print('Detektált egyenesek száma:', len(lines))
        for i in range(0, len(lines)):
            rho = lines[i][0][0]
            theta = lines[i][0][1]
            a = math.cos(theta)
            b = math.sin(theta)
            x0 = a * rho
            y0 = b * rho
            # print('theta: ', math.radians(theta))
            act_deg = theta * 180 / math.pi
            # print('theta: ', act_deg)

            pt1 = (int(x0 + sizemax * (-b)), int(y0 + sizemax * a))
            pt2 = (int(x0 - sizemax * (-b)), int(y0 - sizemax * a))

            if 0 <= act_deg < 45:
                cv2.line(cdst, pt1, pt2, (0, 0, 255), 3, cv2.LINE_AA)
                all_deg = all_deg + act_deg + 90
                # print('0-45', act_deg)

            elif act_deg > 135:
                cv2.line(cdst, pt1, pt2, (0, 0, 255), 3, cv2.LINE_AA)
                all_deg = all_deg + act_deg - 90
                # print('135+', act_deg)

            else:
                cv2.line(cdst, pt1, pt2, (255, 0, 0), 3, cv2.LINE_AA)
                # print('45-135', act_deg)
                all_deg = all_deg + act_deg
            # cv2.imshow('hugh', cdst)
            # cv2.waitKey(0)

    avr = all_deg / len(lines)
    # print('avr: ', avr)

    rows, cols = img.shape[:2]
    m = cv2.getRotationMatrix2D((cols / 2, rows / 2), avr - 90, 1)
    # print('rotate: ', avr - 90)
    rot = cv2.warpAffine(hugh, m, (cols, rows))
    binary = cv2.warpAffine(binary, m, (cols, rows))
    resized = cv2.warpAffine(resized, m, (cols, rows))
    img = cv2.warpAffine(img, m, (cols, rows))

    # cv2.imshow('rot', rot)
    # cv2.imshow('binary', binary)
    # cv2.imshow('resized', resized)
    # cv2.imshow('img13', img)
    # cv2.imwrite('rot.png', rot)


def morphological_transform():
    global elements, bar_hs, chart_with_bars_img, bars
    # cv2.imshow('chart_with_bars_img', chart_with_bars_img)
    retval = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    bars = cv2.dilate(detects.chart_with_bars_img, retval)
    bars = cv2.erode(bars, retval, None, None, 7)
    bars = cv2.erode(bars, retval, None, None, 7)
    bars = cv2.dilate(bars, retval, None, None, 4)
    bars = cv2.dilate(bars, retval, None, None, 4)
    # cv2.imshow('bars', bars)
    bars_p = np.ndarray(bars.shape)
    bars_p.fill(0)
    bars_p[bars > 0] = 255
    bars = np.uint8(bars_p)
    # cv2.imwrite('bars1.png', bars)

    ret_val, labels, stats, centoids = cv2.connectedComponentsWithStats(bars, None, 8)
    # cv2.imshow('bars', bars)
    # print('stat_len: ', len(stats))
    # print('stats2: ', stats)
    elements = stats.copy()

    # Háttér kitörlése
    elements = np.delete(elements, 0, 0)
