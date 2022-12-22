import math

import cv2
import numpy as np
import pytesseract
import re
import matplotlib.pyplot as plt
# import pylatex as pl
import pylatex.tikz
from pylatex import (Document, TikZ, TikZNode,
                     TikZDraw, TikZCoordinate,
                     TikZUserPath, TikZOptions,
                     Subsection, Axis, Plot, Package)

pytesseract.pytesseract.tesseract_cmd = 'D:/Apps/Tesseract/tesseract.exe'
single_digit = r'--oem 3 --psm 10 -c tessedit_char_whitelist=0123456789'
config_title = r'--oem 3 --psm 7'


# todo
# masik betutipus
# labels, cim
# szinek

def read():
    # Beolvasás
    global img, img_orig
    # img_orig = cv2.imread('chart_xbar.png', cv2.IMREAD_GRAYSCALE)

    # img_orig = cv2.imread('chart_ybar.png', cv2.IMREAD_GRAYSCALE)
    # img_orig = cv2.imread('chart_ybar_r.png', cv2.IMREAD_GRAYSCALE)

    # img_orig = cv2.imread('chart_xbar_ex.png', cv2.IMREAD_GRAYSCALE)

    # img_orig = cv2.imread('chart_longtitle.png', cv2.IMREAD_GRAYSCALE)
    # img_orig = cv2.imread('chart_stacked.png', cv2.IMREAD_GRAYSCALE)
    img_orig = cv2.imread('chart_title.png', cv2.IMREAD_GRAYSCALE)

    # img_orig = cv2.imread('chart_ybar_ex.png', cv2.IMREAD_GRAYSCALE)
    # img_orig = cv2.imread('xbar_rotate_l.png', cv2.IMREAD_GRAYSCALE)
    # img_orig = cv2.imread('xbar_rotate_r.png', cv2.IMREAD_GRAYSCALE)
    img = img_orig.copy()
    # cv2.imshow('chart', img)


def upscale():
    # Felskálázás
    global img, num_size, percent, resized
    percent = 2
    width = int(img.shape[1] * percent)
    height = int(img.shape[0] * percent)
    img = cv2.resize(img, (width, height))
    num_size = img.shape[0] * img.shape[1] / 1000
    # print(img.shape[0]*img.shape[1])
    print('num_size: ', num_size)
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
    binary[img < 220] = 255
    binary = np.uint8(binary)
    # cv2.imshow('binary', binary)
    # cv2.imwrite('binary_xbar.png', binary)
    hugh = cv2.Canny(img, 50, 200, None, 3)


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
        print('Detektált egyenesek száma:', len(lines))
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
    print('avr: ', avr)

    rows, cols = img.shape[:2]
    m = cv2.getRotationMatrix2D((cols / 2, rows / 2), avr - 90, 1)
    print('rotate: ', avr - 90)
    rot = cv2.warpAffine(hugh, m, (cols, rows))
    binary = cv2.warpAffine(binary, m, (cols, rows))
    resized = cv2.warpAffine(resized, m, (cols, rows))
    img = cv2.warpAffine(img, m, (cols, rows))

    # cv2.imshow('rot', rot)
    # cv2.imshow('binary', binary)
    # cv2.imshow('resized', resized)
    # cv2.imshow('img13', img)
    # cv2.imwrite('rot.png', rot)


def connected_components():
    # Összefüggő elemek keresése
    global binary, num_size, percent, resized, chart_with_bars_img, numbers, centoids, stats, max_y, new_numbers, chart_title
    # cv2.imshow('binary', binary)
    ret_val, labels, stats, centoids = cv2.connectedComponentsWithStats(binary, None, 8)
    # print('cent: ', centoids)
    i = 1
    print(binary.shape)
    x_half = binary.shape[0] / 3
    y_half = binary.shape[1] / 3

    # todo

    column = []
    row = []
    # print(centoids)
    # print()

    while i < len(stats):
        if stats[i][0] < x_half:
            # print('c: ', centoids[i], centoids[i][0] - centoids[i-1][0], centoids[i][0]/10)
            column.append(stats[i])

        if stats[i][1] > y_half:
            # print('r: ', centoids[i])
            row.append(stats[i])

        i += 1

    j = 0
    std_c = 100
    std_r = 100

    while std_c > 10 or std_r > 10:
        print(j, '. iteration')

        sum_c = 0
        for c in column:
            sum_c += c[0]

        mean_c = sum_c / len(column)

        c_final = []
        c_x = []
        for x in column:
            c_x.append(x[0])
        std_c = np.std(c_x)

        for c in column:
            # print(c, abs(c[0] - mean_c), std_c)
            if abs(c[0] - mean_c) < std_c or std_c < 5:
                c_final.append(c)
        column = c_final

        ########################################

        sum_r = 0
        for r in row:
            sum_r += r[1]

        mean_r = sum_r / len(row)

        r_final = []
        r_y = []
        for y in row:
            r_y.append(y[1])

        std_r = np.std(r_y)
        for r in row:
            if abs(r[1] - mean_r) < std_r or std_r < 5:
                r_final.append(r)
        row = r_final

        j += 1

        print('std_c: ', std_c, 'len_c: ', len(c_final))
        print('std_r: ', std_r, 'len_r: ', len(r_final))
        print('c_final: ', c_final)
        print('r_final: ', r_final)
        print()

    number_stats = np.concatenate((c_final, r_final), axis=0)
    labels_norm = cv2.normalize(labels, None, 0, 65535, cv2.NORM_MINMAX)
    numbers = []
    res = []
    big_res = []
    for stat in stats:
        if stat[4] < num_size:
            res.append(stat[2] * stat[3])
        else:
            big_res.append(stat)

    res_max = max(res) + 10
    print('max: ' + str(res_max))
    chart_with_bars = big_res[1]
    print(chart_with_bars)
    chart_with_bars_img = binary.copy()

    # cv2.imshow('resiz', resized)
    # chart_title = pytesseract.pytesseract.image_to_string(resized, config=config_title)
    # print('chart_title: ', chart_title)

    # print(stats)

    for stat in number_stats:
        if stat[2] * stat[3] <= res_max:
            numbers.append(stat)
            res.append(stat)
            start = (stat[0], stat[1])
            end = (stat[0] + stat[2], stat[1] + stat[3])
            # cv2.rectangle(labels_norm, start, end, 65535)
            cv2.rectangle(resized, start, end, 0, 2)

    labels_norm = np.uint8(labels_norm)
    # percent = 0.8
    # width = int(labels_norm.shape[1] * percent)
    # height = int(labels_norm.shape[0] * percent)
    # labels_norm = cv2.resize(labels_norm, (width, height))
    # cv2.imshow('Labels', labels_norm)

    numbers_str = []
    i = 0

    xplus = int(14 * percent)
    yplus = int(9 * percent)

    print(xplus)
    print(yplus)
    new_numbers = []

    title_img = binary[0:200, 0:]
    title_img = 255 - title_img
    # cv2.imshow('tit', title_img)
    chart_title = pytesseract.pytesseract.image_to_string(title_img, config=config_title)
    # todo
    # chart_title = ''
    print(chart_title)

    for number in numbers:
        x1 = number[0] - xplus
        x2 = number[0] + number[2] + xplus
        y1 = number[1] - yplus
        y2 = number[1] + number[3] + yplus
        # img_re = resized[y1:y2, x1:x2]
        img_re = binary[y1:y2, x1:x2]
        img_re = 255 - img_re
        chart_with_bars_img[y1:y2 - yplus, x1:x2 - xplus] = 0

        title = pytesseract.pytesseract.image_to_string(img_re, config=single_digit)
        numbers_int = re.sub(r'[a-z\n]', '', title.lower())
        numbers_str.append(numbers_int)
        # cv2.imshow(str(numbers_int)+': '+str(i)+'.', img_re)
        # cv2.imwrite(str(numbers_int) + ': ' + str(i)+'.png', img_re)
        i += 1

    has_none = False
    j = 0
    for number in numbers_str:
        if number == '':
            if numbers_str[j - 1] != '':
                numbers_str[j] = int(numbers_str[j - 1]) - 1
            elif numbers_str[j + 1] != '':
                numbers_str[j] = int(numbers_str[j + 1]) + 1
            numbers_str[j] = str(numbers_str[j])
        j += 1

    print('numbers: ', numbers_str)
    j = 0
    for number in numbers:
        x2 = number[0] + number[2] + xplus
        y2 = number[1] + number[3] + yplus
        number = np.append(number, int(numbers_str[j]))
        new_numbers.append(number)
        cv2.putText(resized, numbers_str[j], (x2 - xplus, y2), cv2.QT_FONT_NORMAL, 1, 0, 2)
        j += 1

    print('has none: ', has_none)

    # cv2.imwrite('rects.png', resized)
    # cv2.imshow('rects', resized)
    # cv2.imwrite('chart_with_bars_img.png', chart_with_bars_img)
    print()
    print('Kompenensek száma:', len(numbers))

    # print('numbers: ', numbers)


def morphological_transform():
    global elements, bar_hs, chart_with_bars_img, bars
    # cv2.imshow('chart_with_bars_img', chart_with_bars_img)
    retval = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    bars = cv2.dilate(chart_with_bars_img, retval)
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
    print('stat_len: ', len(stats))
    print('stats2: ', stats)
    elements = stats.copy()
    bar_hs = []

    # Háttér kitörlése
    elements = np.delete(elements, 0, 0)


def define_orientation():
    global elements, bar_hs, bars, ratios, new_numbers, numbers, orientation, resized

    # Legnagyobb oszlop, orientáció
    max_full = elements[0]

    # Rendezés adott tengely szerint
    if max_full[0] > max_full[2]:
        x_v = 3
        f_or_s = 0
        orientation = 'ybar'
        max_y = new_numbers[0]

    else:
        x_v = 2
        f_or_s = 1
        orientation = 'xbar'
        max_y = new_numbers[-1]

    print('max y: ', max_y)
    # print('centoids: ', centoids)
    print('stats: ', stats)

    for element in elements:
        if element[x_v] > max_full[x_v]:
            max_full = element
    print('max: ', max_full)
    elements = sorted(elements, key=lambda x: x[f_or_s])
    for element in elements:
        bar_hs.append(element[x_v])
    max_bar = max(bar_hs)
    ratios = np.round(bar_hs / max_full[x_v], 2)

    print('orientation: ', orientation)
    print('bar_hs: ', bar_hs)
    print('max_bar: ', max_bar)
    print('elements: ', elements)
    print('ratios: ', ratios)

    # Visszaskálázás
    percent = 2
    width = int(resized.shape[1] / percent)
    height = int(resized.shape[0] / percent)
    resized = cv2.resize(resized, (width, height))

    # cv2.imshow('rects_' + orientation, resized)
    # cv2.imwrite('rects_'+orientation+'.png', resized)
    # cv2.imwrite('bars_'+orientation+'.png', bars)


def to_latex():
    global orientation, ratios, max_y, new_numbers
    ratios = ratios * (new_numbers[0][5] - 1)
    # todo 5 a max, 4 kell
    x = [1, 2, 3, 4]
    y = ratios

    if orientation == 'xbar':
        y = np.flip(y)
        # y = sorted(y, reverse=True)
        plt.barh(x, y, 0.25)
    else:
        plt.bar(x, y, 0.25)

    # plt.title()
    # plt.xlabel()
    # plt.ylabel()
    plt.show()

    ratios = ratios / new_numbers[0][5]


def latex():
    global orientation, ratios, max_y, new_numbers, chart_title
    ratios = ratios * new_numbers[0][5]
    print('coordinates: ', ratios)
    # todo 5 a max, 4 kell
    length = len(ratios)
    doc = Document()

    # doc.packages.append(Package('fontspec'))
    # doc.packages.append(Package('sansmath'))

    coordinates = []
    i = 0

    if orientation == 'xbar':
        ratios = np.flip(ratios)
        while i < length:
            coordinates.append((ratios[i], i + 1))
            i += 1

    elif orientation == 'ybar':
        # ratios = np.flip(ratios)
        while i < length:
            # coordinates.append((ratios[i], i+1))
            coordinates.append((i + 1, ratios[i]))
            i += 1

    print(coordinates)
    with doc.create(TikZ()):
        with doc.create(TikZ()):
            # plot_options = orientation + ', title style={align=left}, ymin = 0, ymax = 9, xmin = 0, xmax = 9'
            plot_options = orientation + ', title = '+chart_title
            with doc.create(Axis(options=plot_options)) as plot:
                plot.append(Plot(coordinates=coordinates))

    doc.generate_pdf('tikzdraw', clean_tex=False, compiler='pdfLaTeX')


if __name__ == "__main__":
    read()
    upscale()
    treshold()
    create_binary()
    rotate()
    connected_components()
    morphological_transform()
    define_orientation()
    # to_latex()
    latex()
    cv2.waitKey(0)
    cv2.destroyAllWindows()
