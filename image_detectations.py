import re
import cv2
import numpy as np
import pytesseract
import image_edits as edits


pytesseract.pytesseract.tesseract_cmd = 'D:/Apps/Tesseract/tesseract.exe'
single_digit = r'--oem 3 --psm 10 -c tessedit_char_whitelist=0123456789'
config_title = r'--oem 3 --psm 7'

chart_with_bars_img = None
ratios = None
new_numbers = None
orientation = None
chart_title = None
c_new_numbers = None
r_new_numbers = None

# todo
# masik betutipus
# labels, cim
# szinek

def connected_components():
    # Összefüggő elemek keresése
    global binary, num_size, percent, resized, chart_with_bars_img, numbers, centoids, stats, max_y, new_numbers, chart_title, r_numbers, c_numbers, c_new_numbers, r_new_numbers
    resized = edits.resized
    binary = edits.create_binary()
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


    for i in range(0, len(r_final)-1):
        for j in range(0, len(r_final)-i-1):
            if r_final[j][0] < r_final[j+1][0]:
                r_final[j], r_final[j + 1] = r_final[j + 1], r_final[j]



    number_stats = np.concatenate((c_final, r_final), axis=0)
    labels_norm = cv2.normalize(labels, None, 0, 65535, cv2.NORM_MINMAX)
    numbers = []
    res = []
    big_res = []
    for stat in stats:
        if stat[4] < edits.num_size:
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

    r_numbers = []
    c_numbers = []
    # todo sort és oszlopot meg tudjuk különböztetni
    for row_num in r_final:
        if row_num[2] * row_num[3] <= res_max:
            r_numbers.append(row_num)
            res.append(row_num)
            start = (row_num[0], row_num[1])
            end = (row_num[0] + row_num[2], row_num[1] + row_num[3])
            # cv2.rectangle(labels_norm, start, end, 65535)
            cv2.rectangle(edits.resized, start, end, 0, 2)

    for col_num in c_final:
        if col_num[2] * col_num[3] <= res_max:
            c_numbers.append(col_num)
            res.append(col_num)
            start = (col_num[0], col_num[1])
            end = (col_num[0] + col_num[2], col_num[1] + col_num[3])
            # cv2.rectangle(labels_norm, start, end, 65535)
            cv2.rectangle(edits.resized, start, end, 0, 3)

    # for stat in number_stats:
    #     if stat[2] * stat[3] <= res_max:
    #         numbers.append(stat)
    #         res.append(stat)
    #         start = (stat[0], stat[1])
    #         end = (stat[0] + stat[2], stat[1] + stat[3])
    #         # cv2.rectangle(labels_norm, start, end, 65535)
    #         cv2.rectangle(edits.resized, start, end, 0, 2)

    labels_norm = np.uint8(labels_norm)
    # percent = 0.8
    # width = int(labels_norm.shape[1] * percent)
    # height = int(labels_norm.shape[0] * percent)
    # labels_norm = cv2.resize(labels_norm, (width, height))
    # cv2.imshow('Labels', labels_norm)
    # print('numbers: ', numbers)
    numbers_str = []
    i = 0
    percent = edits.percent
    xplus = int(14 * percent)
    yplus = int(9 * percent)

    print(xplus)
    print(yplus)
    new_numbers = []
    #
    # for number in numbers:
    #     x1 = number[0] - xplus
    #     x2 = number[0] + number[2] + xplus
    #     y1 = number[1] - yplus
    #     y2 = number[1] + number[3] + yplus
    #     # img_re = resized[y1:y2, x1:x2]
    #     img_re = binary[y1:y2, x1:x2]
    #     img_re = 255 - img_re
    #     chart_with_bars_img[y1:y2 - yplus, x1:x2 - xplus] = 0
    #
    #     title = pytesseract.pytesseract.image_to_string(img_re, config=single_digit)
    #     numbers_int = re.sub(r'[a-z\n]', '', title.lower())
    #     numbers_str.append(numbers_int)
    #     # cv2.imshow(str(numbers_int)+': '+str(i)+'.', img_re)
    #     # cv2.imwrite(str(numbers_int) + ': ' + str(i)+'.png', img_re)
    #     i += 1

    all_numbers = np.concatenate((c_final, r_final), axis=0)

    for number in all_numbers:
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
    r_new_numbers = []
    for r_number in r_numbers:
        x2 = r_number[0] + r_number[2] + xplus
        y2 = r_number[1] + r_number[3] + yplus
        cv2.putText(edits.resized, numbers_str[j], (x2 - xplus, y2), cv2.QT_FONT_NORMAL, 1, 0, 2)
        centoid_x = np.round(r_number[0] + r_number[2]//2)
        centoid_y = np.round(r_number[1] + r_number[3]//2)
        r_number = np.append(r_number, int(centoid_x))
        r_number = np.append(r_number, int(centoid_y))
        r_number = np.append(r_number, int(numbers_str[j]))
        r_new_numbers.append(r_number)
        j += 1

    j = 0
    c_new_numbers = []
    for c_number in c_numbers:
        x2 = c_number[0] + c_number[2] + xplus
        y2 = c_number[1] + c_number[3] + yplus
        cv2.putText(edits.resized, numbers_str[j], (x2 - xplus, y2), cv2.QT_FONT_NORMAL, 1, 0, 2)
        centoid_x = np.round(c_number[0] + c_number[2]//2)
        centoid_y = np.round(c_number[1] + c_number[3]//2)
        c_number = np.append(c_number, int(centoid_x))
        c_number = np.append(c_number, int(centoid_y))
        c_number = np.append(c_number, int(numbers_str[j]))
        c_new_numbers.append(c_number)
        j += 1


    # for number in numbers:
    #     x2 = number[0] + number[2] + xplus
    #     y2 = number[1] + number[3] + yplus
    #     number = np.append(number, int(numbers_str[j]))
    #     new_numbers.append(number)
    #     cv2.putText(edits.resized, numbers_str[j], (x2 - xplus, y2), cv2.QT_FONT_NORMAL, 1, 0, 2)
    #     j += 1

    print('has none: ', has_none)

    cv2.imwrite('rects.png', resized)
    # cv2.imshow('rects', resized)
    # cv2.imwrite('chart_with_bars_img.png', chart_with_bars_img)
    print()
    print('Kompenensek száma:', len(r_numbers) + len(c_numbers))

    # print('numbers: ', numbers)


    # print('cmin:', c_new_numbers[-1])
    # print('cmax:', c_new_numbers[0])
    # print('dist: ', c_new_numbers[-1][6] - c_new_numbers[0][6], ', unit: ', c_new_numbers[0][7])

    print()
    print('rmin:', r_new_numbers[-1])
    print('rmax:', r_new_numbers[0])
    print('dist: ', r_new_numbers[0][5] - r_new_numbers[-1][5], ', unit: ', r_new_numbers[0][7])
    print('1 unit: ', (r_new_numbers[0][5] - r_new_numbers[-1][5])/r_new_numbers[0][7])
    print('1 unit: ', r_new_numbers[0][7] / (r_new_numbers[0][5] - r_new_numbers[-1][5]))


def detect_title():

    title_img = binary[0:200, 0:]



    title_img = 255 - title_img
    # cv2.imshow('tit', title_img)
    chart_title = pytesseract.pytesseract.image_to_string(title_img, config=config_title)
    # todo
    # chart_title = ''
    print(chart_title)
    return chart_title

def define_orientation():
    global elements, bar_hs, bars, ratios, numbers, orientation, resized, r_numbers, c_numbers, c_new_numbers, r_new_numbers
    resized = edits.resized
    elements = edits.elements
    bar_hs = []
    # Legnagyobb oszlop, orientáció
    max_full = elements[0]
    print('max_full: ', max_full)
    print('r_new_numbers: ', r_new_numbers)
    print('c_new_numbers: ', c_new_numbers)

    # Rendezés adott tengely szerint
    if max_full[0] > max_full[2]:
        x_v = 3
        f_or_s = 0
        orientation = 'ybar'
        max_y = c_new_numbers[0]

    else:
        x_v = 2
        f_or_s = 1
        orientation = 'xbar'
        max_y = r_new_numbers[0]

    print('max y: ', max_y)
    # print('centoids: ', centoids)
    # print('stats: ', stats)

    for element in elements:
        if element[x_v] > max_full[x_v]:
            max_full = element
    print('max: ', max_full)
    elements = sorted(elements, key=lambda x: x[f_or_s])
    for element in elements:
        bar_hs.append(element[x_v])
    max_bar = max(bar_hs)
    #ratios = np.round(bar_hs / max_full[x_v], 2)
    ratios = np.round(bar_hs / (r_new_numbers[0][5] - r_new_numbers[-1][5]), 2)

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