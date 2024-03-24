import re

import cv2
import numpy as np
import pytesseract

import functions.detect_legend as legend_detections
import functions.image_edits as edits

pytesseract.pytesseract.tesseract_cmd = 'D:/Apps/Tesseract/tesseract.exe'
# single_digit = r'--oem 3 --psm 10 -c tessedit_char_whitelist=0123456789'
single_digit = r'--oem 3 --psm 7 -c tessedit_char_whitelist=0123456789'
multi_digits = r'--oem 3 --psm 6 outputbase digits tessedit_char_whitelist=0123456789 '

config_title = r'--oem 3 --psm 7'

chart_with_bars_img = None
ratios = None
new_numbers = None
orientation = None
chart_title = None
r_final = []
c_final = []
r_new_numbers = []
c_new_numbers = []
col_nums = []
row_nums = []
resized_gray = None
binary = None
legend_orig = None
simple_chart_bar_color = None
tick_number_of_longest_bar = None
grouped_bars_with_data = None
average_character_height = None


# Fill two arrays with values from each x and y coordinate axes
def isolate_x_y() -> None:
    """

    """
    global resized_gray, binary, col_nums, row_nums, number_of_components, labels, stats, centoids

    resized = edits.resized_gray
    binary = edits.threshold()

    # number_of_components = background included
    # labels = matrix, 0-background, 1-component
    # stats = enclosing rectangle upper left point, width, length, number of pixels
    # centoids = center points of object
    number_of_components, labels, stats, centoids = cv2.connectedComponentsWithStats(binary, None, 8)

    # searching in the left third for y-axis and bottom third for x-axis of the picture
    row_third = binary.shape[0] / 3
    col_third = binary.shape[1] / 3
    row_nums = []
    col_nums = []
    for i in range(1, number_of_components):
        if stats[i][0] < row_third:
            col_nums.append(stats[i])

        if stats[i][1] > col_third:
            row_nums.append(stats[i])


def connected_components():
    global binary, num_size, percent, resized_gray, chart_with_bars_img, numbers, centoids, stats, max_y, new_numbers, \
        chart_title, r_numbers, c_numbers, elements, numbers_str, xplus, yplus, col_nums, row_nums, \
        r_final, c_final, c_numbers_str, r_numbers_str, labels, average_character_height

    isolate_x_y()
    cut_outstandings()

    average_character_height = int(np.mean(np.array(r_final)[:, 3]))
    print(f"\taverage_height {average_character_height}")

    cut_column_outliers()

    # print("\t\nc_final before sort \n\t" + "\n\t".join(map(str, c_final)))
    temp_c_final = sorted(c_final, key=lambda x: (x[1], x[0]))
    c_final = temp_c_final
    # print("\t\nc_final after sort \n\t" + "\n\t".join(map(str, c_final)))

    # print("\tr_final before merge \n\t" + "\n\t".join(map(str, r_final)))
    r_final = merge_multi_digit_numbers(r_final, False)
    # print("\tr_final after merge \n\t" + "\n\t".join(map(str, r_final)))

    # print("\t\nc_final before merge \n\t" + "\n\t".join(map(str, c_final)))
    c_final = merge_multi_digit_numbers(c_final, True)
    # print("\t\nc_final after merge \n\t" + "\n\t".join(map(str, c_final)))

    temp_r_final = sorted(r_final, key=lambda x: x[0], reverse=True)
    # print("\tr_final after sort \n\t" + "\n\t".join(map(str, temp_r_final)))

    # number_stats = np.concatenate((c_final, r_final), axis=0)
    labels_norm = cv2.normalize(labels, None, 0, 65535, cv2.NORM_MINMAX)
    numbers = []
    res = []
    big_res = []
    for stat in stats:
        if stat[4] < edits.NUM_SIZE:
            res.append(stat[2] * stat[3])
        else:
            big_res.append(stat)

    res_max = max(res) + 10
    chart_with_bars_img = binary.copy()

    r_numbers = []
    c_numbers = []
    for row_num in r_final:
        r_numbers.append(row_num)
        res.append(row_num)
        start = (row_num[0], row_num[1])
        end = (row_num[0] + row_num[2], row_num[1] + row_num[3])
        cv2.rectangle(edits.resized_gray, start, end, 0, 2)

    # edits.imshow_resized("r_final", edits.resized_gray)
    for col_num in c_final:
        c_numbers.append(col_num)
        res.append(col_num)
        start = (col_num[0], col_num[1])
        end = (col_num[0] + col_num[2], col_num[1] + col_num[3])
        cv2.rectangle(edits.resized_gray, start, end, 0, 3)

    numbers_str = []
    i = 0
    percent = edits.UPSCALE_RATE
    xplus = int(10 * percent)
    yplus = int(9 * percent)

    new_numbers = []
    c_numbers_str = []

    ret_val, labels, stats, centoids = cv2.connectedComponentsWithStats(binary, None, 8)
    sorted_stats = sorted(stats, key=lambda x: x[4], reverse=True)
    stats_max = sorted_stats[1]
    x1 = stats_max[0]
    x2 = x1 + stats_max[2]
    y1 = stats_max[1]
    y2 = y1 + stats_max[3]

    img_b = binary
    img_b[y1:y2, x1:x2] = 0

    # Delete commas and small objects
    for stat in sorted_stats:
        if stat[2] < average_character_height * 0.7 and stat[3] < average_character_height * 0.7:
            x1 = stat[0]
            x2 = x1 + stat[2]
            y1 = stat[1]
            y2 = y1 + stat[3]
            img_b[y1:y2, x1:x2] = 0

    for number in c_final:
        x1 = number[0] - xplus
        x2 = number[0] + number[2] + xplus
        y1 = number[1] - yplus
        y2 = number[1] + number[3] + yplus

        img_re = img_b[y1:y2, x1:x2]
        img_re = 255 - img_re
        chart_with_bars_img[y1:y2 - yplus, x1:x2 - xplus] = 0

        title = pytesseract.pytesseract.image_to_string(img_re, config=multi_digits)
        title = re.sub(r'[\n]', '', title)
        c_numbers_str.append(title)
        i += 1

    r_numbers_str = []
    for number in r_final:
        x1 = number[0] - xplus
        x2 = number[0] + number[2] + xplus
        y1 = number[1] - yplus
        y2 = number[1] + number[3] + yplus
        img_re = img_b[y1:y2, x1:x2]
        img_re = 255 - img_re
        chart_with_bars_img[y1:y2 - yplus, x1:x2 - xplus] = 0

        title = pytesseract.pytesseract.image_to_string(img_re, config=multi_digits)
        title = re.sub(r'[\n]', '', title)
        r_numbers_str.append(title)
        # cv2.imshow(f"xnumber{i}. {title}", img_re)

        # cv2.imshow("xnumber" + str(title) + ': ' + str(i) + '.', img_re)
        # cv2.imshow("xnumber"+str(title) + ': ' + str(i) + '.', img_re)
        # cv2.imwrite(str(numbers_int) + ': ' + str(i)+'.png', img_re)
        i += 1

    # print('r_numbers_str: ', r_numbers_str)
    row_type = None
    row_type = 'str'
    row_type = 'int'
    col_type = None
    col_type = 'str'
    col_type = 'int'

    if row_type == 'int':
        row_int()
    # elif row_type == 'str':
    #     row_str()

    # if col_type == 'int':
    #     col_int()
    # elif col_type == 'str':
    #    col_str()

    # col_str()


def cut_column_outliers():
    global col_nums, c_final
    j = 0
    centoid_distances = 100

    gray_copy_1 = edits.img_gray.copy()
    gray_copy_2 = edits.img_gray.copy()

    for num in col_nums:
        start = (num[0], num[1])
        end = (num[0] + num[2], num[1] + num[3])
        cv2.rectangle(gray_copy_1, start, end, 0, 2)
        # edits.imshow_resized("resized_gray before cut", gray_copy_1)

    while centoid_distances > average_character_height and j < len(col_nums):
        # print(f"\n\t{j + 1}. iteration")

        x_of_centoids = []

        for num in col_nums:
            num_centoid_x = int((num[0] + num[2]) / 2)
            x_of_centoids.append(num_centoid_x)
        # print(f"\tx_of_centoids {x_of_centoids}")

        average_centoid = np.mean(np.array(x_of_centoids))
        # print(f"\taverage_centoid {average_centoid}")

        centoid_distances = np.std(x_of_centoids)
        # print(f"\tdistance {centoid_distances}")

        cutoff = centoid_distances * 2

        c_final = []
        for num in col_nums:
            centoid_x = int((num[0] + num[2]) / 2)
            #
            if abs(centoid_x - average_centoid) < cutoff:
                c_final.append(num)
        col_nums = c_final
        j += 1

    for num in col_nums:
        start = (num[0], num[1])
        end = (num[0] + num[2], num[1] + num[3])
        cv2.rectangle(gray_copy_2, start, end, 0, 2)
        # edits.imshow_resized("resized_gray after cut", gray_copy_2)


def cut_outstandings():
    global col_nums, row_nums, r_final, c_final
    j = 0
    std_c = 100
    std_r = 100
    local_col_nums = col_nums
    local_row_nums = row_nums
    print("\nrow_nums \n\t" + "\n\t".join(map(str, row_nums)))

    while std_r > 10 and j < len(row_nums):
        # print(j, '. iteration')

        # sum_c = 0
        # # x coordinate of column values
        # for c in col_nums:
        #     sum_c += c[0]
        #
        # mean_c = sum_c / len(col_nums)
        #
        # c_final = []
        # c_x = []
        # for x in col_nums:
        #     c_x.append(x[0])
        # std_c = np.std(c_x)
        #
        # for c in col_nums:
        #     # print(c, abs(c[0] - mean_c), std_c)
        #     if abs(c[0] - mean_c) < std_c or std_c < 5:
        #         c_final.append(c)
        # col_nums = c_final

        ########################################

        sum_r = 0
        for r in row_nums:
            sum_r += r[1]

        mean_r = sum_r / len(row_nums)

        r_final = []
        r_y = []
        for y in row_nums:
            r_y.append(y[1])

        std_r = np.std(r_y)
        for r in row_nums:
            if abs(r[1] - mean_r) < std_r or std_r < 5:
                r_final.append(r)
        row_nums = r_final

        j += 1


def merge_multi_digit_numbers(numbers, column):
    temp_numbers = []
    # Width of a number is unknown, if all the numbers are multi digit numbers, instead use the height
    threshold = average_character_height

    for i in range(len(numbers)):
        # Check if not component of a multi digit number
        if len(numbers[i]) > 1:
            i_x = numbers[i][0]
            i_y = numbers[i][1]
            i_w = numbers[i][2]
            i_h = numbers[i][3]
            i_pixels = numbers[i][4]
            i_centoid_y = (i_y + i_h) / 2

            multi_digit_number = []

            for j in range(i + 1, len(numbers)):
                # Check if not component of a multi digit number
                if len(numbers[j]) > 1:
                    j_x = numbers[j][0]
                    j_y = numbers[j][1]
                    j_w = numbers[j][2]
                    j_h = numbers[j][3]
                    j_pixels = numbers[j][4]
                    j_centoid_y = (j_y + j_h) / 2

                    # Break if number is from another column tick
                    if column and abs(i_centoid_y - j_centoid_y) >= threshold:
                        break

                    # If end of number is close to another number
                    if abs((i_x + i_w) - j_x) <= threshold:
                        # Set empty array for multi digit number parts
                        print(f"\n\tdeleted i {numbers[i]}")
                        print(f"\tdeleted j {numbers[j]}")

                        numbers[i] = [0]
                        numbers[j] = [0]
                        # Add multi digit number
                        multi_digit_number = [i_x, i_y, j_x + j_w - i_x, i_h, i_pixels + j_pixels]
                        print(f"\tadded     {multi_digit_number}")

                        i_x = multi_digit_number[0]
                        i_y = multi_digit_number[1]
                        i_w = multi_digit_number[2]
                        i_h = multi_digit_number[3]
                        i_pixels = multi_digit_number[4]

            # Check if still not component of a multi digit number
            if len(numbers[i]) > 1:
                temp_numbers.append(numbers[i])
            else:
                temp_numbers.append(multi_digit_number)

    return temp_numbers


# def col_str():
#     global numbers_str, xplus, yplus
#
#     has_none = False
#     j = 0
#
#     for number in numbers_str:
#         if number == '':
#             if numbers_str[j - 1] != '':
#                 numbers_str[j] = int(numbers_str[j - 1]) - 1
#             elif numbers_str[j + 1] != '':
#                 numbers_str[j] = int(numbers_str[j + 1]) + 1
#             numbers_str[j] = str(numbers_str[j])
#         j += 1
#
#     j = 0
#
#     for c_number in c_numbers:
#         x2 = c_number[0] + c_number[2] + xplus
#         y2 = c_number[1] + c_number[3] + yplus
#         cv2.putText(edits.resized, numbers_str[j], (x2 - xplus, y2), cv2.QT_FONT_NORMAL, 1, 0, 2)
#         centoid_x = np.round(c_number[0] + c_number[2]//2)
#         centoid_y = np.round(c_number[1] + c_number[3]//2)
#         c_number = np.append(c_number, int(centoid_x))
#         c_number = np.append(c_number, int(centoid_y))
#         c_number = np.append(c_number, int(numbers_str[j]))
#         c_new_numbers.append(c_number)
#         j += 1
#
#
#     for r_number in r_numbers:
#         x2 = r_number[0] + r_number[2] + xplus
#         y2 = r_number[1] + r_number[3] + yplus
#         cv2.putText(edits.resized, numbers_str[j], (x2 - xplus, y2), cv2.QT_FONT_NORMAL, 1, 0, 2)
#         centoid_x = np.round(r_number[0] + r_number[2]//2)
#         centoid_y = np.round(r_number[1] + r_number[3]//2)
#         r_number = np.append(r_number, int(centoid_x))
#         r_number = np.append(r_number, int(centoid_y))
#         r_number = np.append(r_number, int(numbers_str[j]))
#         r_new_numbers.append(r_number)
#         j += 1


def row_int():
    global numbers_str, xplus, yplus, c_numbers_str, r_numbers_str, r_new_numbers, c_new_numbers
    numbers_str = np.concatenate((c_numbers_str, r_numbers_str), axis=0)

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

    print('\tnumbers: ', numbers_str)
    print('\tc_numbers: ', c_new_numbers)
    print('\tnumbers_str: ', numbers_str)
    j = 0

    for c_number in c_numbers:
        x2 = c_number[0] + c_number[2] + xplus
        y2 = c_number[1] + c_number[3] + yplus
        cv2.putText(edits.resized_gray, numbers_str[j], (x2 - xplus, y2), cv2.QT_FONT_NORMAL, 1, 0, 2)
        centoid_x = np.round(c_number[0] + c_number[2] // 2)
        centoid_y = np.round(c_number[1] + c_number[3] // 2)
        c_number = np.append(c_number, int(centoid_x))
        c_number = np.append(c_number, int(centoid_y))
        c_number = np.append(c_number, int(numbers_str[j]))
        c_new_numbers.append(c_number)
        j += 1

    for r_number in r_numbers:
        x2 = r_number[0] + r_number[2] + xplus
        y2 = r_number[1] + r_number[3] + yplus
        cv2.putText(edits.resized_gray, numbers_str[j], (x2 - xplus, y2), cv2.QT_FONT_NORMAL, 1, 0, 2)
        centoid_x = np.round(r_number[0] + r_number[2] // 2)
        centoid_y = np.round(r_number[1] + r_number[3] // 2)
        r_number = np.append(r_number, int(centoid_x))
        r_number = np.append(r_number, int(centoid_y))
        r_number = np.append(r_number, int(numbers_str[j]))
        r_new_numbers.append(r_number)
        j += 1

    print('\tnumbers: ', numbers)


def detect_title(has_title):
    if has_title == 0:
        return None
    elif has_title == 1:
        title_img = binary[0:200, 0:]
    elif has_title == -1:
        title_img = binary[-200:, 0:]

    title_img = 255 - title_img
    chart_title = pytesseract.pytesseract.image_to_string(title_img, config=config_title)
    print(f"\t Detected title: {chart_title}")
    return chart_title


def bars():
    global mean
    elements = edits.elements
    new_elements = []
    for bar in elements:
        start = bar[1] + bar[3]
        bar = np.append(bar, start)
        new_elements.append(bar)

    elements = new_elements
    sum = 0
    for bar in elements:
        sum += bar[5]
    mean = sum / len(elements)


def define_orientation():
    global elements, bar_hs, bars, ratios, numbers, orientation, resized_gray, r_numbers, c_numbers, mean
    resized = edits.resized_gray
    elements = edits.elements
    bar_hs = []

    # Select biggest bar
    sorted_elements = sorted(elements, key=lambda x: x[4], reverse=True)
    max_full = sorted_elements[0]

    # Rendezés adott tengely szerint
    if max_full[3] > max_full[1]:
        x_v = 3
        f_or_s = 0
        orientation = 'ybar'
        max_y = c_new_numbers[0]

    else:
        x_v = 2
        f_or_s = 1
        orientation = 'xbar'
        max_y = r_new_numbers[0]

    print(f"\t{'Horizontal' if orientation == 'xbar' else 'Vertical'} chart detected")

    # for element in elements:
    #     if element[x_v] > max_full[x_v]:
    #         max_full = element
    elements = sorted(elements, key=lambda x: x[f_or_s])
    for element in elements:
        bar_hs.append(element[x_v])
    max_bar = max(bar_hs)

    # Visszaskálázás
    percent = 2
    width = int(resized.shape[1] / percent)
    height = int(resized.shape[0] / percent)
    resized = cv2.resize(resized, (width, height))
    cv2.imwrite('rects_' + orientation + '.png', resized)
    # cv2.imwrite('bars_'+orientation+'.png', bars)


# def define_ratios(grouped, bars_with_data):
#     global bar_hs, ratios, orientation, r_new_numbers, c_new_numbers, mean
#
#     if grouped:
#         if orientation == 'xbar':
#             # Search the longest bar and save the width
#             max_bar_width = 0
#             for key, values in bars_with_data.items():
#                 for bar_data in values["bars"]:
#                     max_bar_width = max(bar_data["w"], max_bar_width)
#
#             # Add the current bar width / the longest bar width
#             for key, values in bars_with_data.items():
#                 for bar_data in values["bars"]:
#                     bar_data["ratio"] = round(bar_data["w"] / max_bar_width, 2)
#
#             print("\tdefine_ratios bars_with_data: {\n\t\t" + "\n\t\t".join(
#                 f"{key}: {values}" for key, values in bars_with_data.items()) + "}")
#
#         elif orientation == 'ybar':
#             # ratios = np.round(bar_hs / (mean - c_new_numbers[0][6]), 2)
#
#             # Search the highest bar and save the height
#             max_bar_height = 0
#             for key, values in bars_with_data.items():
#                 for bar_data in values["bars"]:
#                     max_bar_height = max(bar_data["h"], max_bar_height)
#
#             # Add the current bar height / the highest bar height
#             for key, values in bars_with_data.items():
#                 for bar_data in values["bars"]:
#                     bar_data["ratio"] = round(bar_data["h"] / max_bar_height, 2)
#
#             print("\tdefine_ratios bars_with_data: {\n\t\t" + "\n\t\t".join(
#                 f"{key}: {values}" for key, values in bars_with_data.items()) + "}")
#
#     else:
#         if orientation == 'xbar':
#             longest_bar = find_closest_tick_number(bars_with_data, r_new_numbers, True)
#             ratios = np.round(bar_hs / longest_bar[2], 2)
#
#         elif orientation == 'ybar':
#             longest_bar = find_closest_tick_number(bars_with_data, c_new_numbers, False)
#             ratios = np.round(bar_hs / longest_bar[3], 2)
#             # ratios = np.round(bar_hs / (mean - c_new_numbers[0][6]), 2)


def define_simple_chart_ratios(bars_with_colors):
    global bar_hs, ratios, orientation, r_new_numbers, c_new_numbers
    if orientation == 'xbar':
        longest_bar = find_longest_bar(bars_with_colors, True)
        ratios = np.round(bar_hs / longest_bar[2], 2)
        longest_bar_object = {
            "x": longest_bar[0],
            "y": longest_bar[1],
            "w": longest_bar[2],
            "h": longest_bar[3],
        }
        find_closest_tick_number(r_new_numbers, longest_bar_object, True)

    elif orientation == 'ybar':
        longest_bar = find_longest_bar(bars_with_colors, False)
        ratios = np.round(bar_hs / longest_bar[3], 2)
        longest_bar_object = {
            "x": longest_bar[0],
            "y": longest_bar[1],
            "w": longest_bar[2],
            "h": longest_bar[3],
        }
        find_closest_tick_number(c_new_numbers, longest_bar_object, False)


def define_grouped_chart_ratios(bars_with_data):
    global orientation, grouped_bars_with_data

    value_name = "w" if orientation == 'xbar' else "h"

    # Search the longest bar
    longest_bar = bars_with_data[0]["bars"][0]
    for key, values in bars_with_data.items():
        for bar_data in values["bars"]:
            if bar_data[value_name] >= longest_bar[value_name]:
                longest_bar = bar_data

    # Add the current bar length / the longest bar length ratio
    for key, values in bars_with_data.items():
        for bar_data in values["bars"]:
            bar_data["ratio"] = round(bar_data[value_name] / longest_bar[value_name], 2)

    grouped_bars_with_data = bars_with_data

    print("\tgrouped_bars_with_data: {\n\t\t" + "\n\t\t".join(
        f"{key}: {values}" for key, values in grouped_bars_with_data.items()) + "}")

    if orientation == 'xbar':
        find_closest_tick_number(r_new_numbers, longest_bar, True)

    elif orientation == 'ybar':
        find_closest_tick_number(r_new_numbers, longest_bar, False)


def find_longest_bar(bars_with_data, horizontal):
    global tick_number_of_longest_bar

    # Set indexes
    if horizontal:
        x_y_index = 0
        w_h_index = 2
        centoid_index = 5
    else:
        x_y_index = 1
        w_h_index = 3
        centoid_index = 6

    longest_bar = bars_with_data[0][0]

    # Find the longest bar
    for bar_data in bars_with_data:
        if bar_data[0][w_h_index] >= longest_bar[w_h_index]:
            longest_bar = bar_data[0]

    print(f"longest_bar: {longest_bar}")
    return longest_bar


def find_closest_tick_number(tick_data, longest_bar, horizontal):
    global tick_number_of_longest_bar

    # Set indexes
    if horizontal:
        x_y_value_name = "x"
        w_h_value_name = "w"
        centoid_index = 5
    else:
        x_y_value_name = "y"
        w_h_value_name = "h"
        centoid_index = 6
    number_index = 7

    closest_number_data = tick_data[0]

    if horizontal:
        bar_end = longest_bar[x_y_value_name] + longest_bar[w_h_value_name]
    else:
        bar_end = longest_bar[x_y_value_name]

    # Find the closest tick
    for number_data in tick_data:
        # print(f"\tnumber_data (x, y):{number_data[:2]},\t(width, height):{number_data[2:4]},centoid_x:{number_data[5]},\tpixels:{number_data[6]},\tnumber: {number_data[7]}")
        if abs(bar_end - number_data[centoid_index]) <= abs(bar_end - closest_number_data[centoid_index]):
            closest_number_data = number_data

    tick_number_of_longest_bar = closest_number_data[number_index]


def detect_colors(img, bar_stats, bars_labels):
    """
    Detects dominant colors of bars
    Args:
        img:
        bar_stats:
        bars_labels:

    Returns:

    """
    bars_with_colors = []
    # bars_stats = edits.elements
    bars_stats_without_legend = []

    # bars_labels = edits.bars_with_labels
    bars_img = np.ndarray(img.shape)
    # print(f"bar_stats: {bar_stats}")
    for i in range(len(bar_stats)):
        bars_img.fill(0)
        color_rgb = detect_bar_color(img, bar_stats, bars_labels, i + 1)
        bars_with_colors.append([bar_stats[i], np.array(color_rgb)])
        # print(f"{i}. (stats: {bar_stats[i]}) \t (color: {color_rgb})")
        bars_img[bars_labels == i + 1] = 255
    return bars_with_colors


def detect_bar_color(resized_color, bars_stats, bars_labels, label):
    """
    Detects the dominant color of a bar
    Args:
        resized_color:
        bars_stats:
        bars_labels:
        label:

    Returns:

    """
    # bars_stats = edits.elements
    # resized_color = edits.resized_color.copy()

    bar_with_color = np.ndarray(resized_color.shape, np.uint8)
    bar_with_color.fill(0)
    bar_with_color[bars_labels == label] = resized_color[bars_labels == label]
    # edits.imshow_resized(f"{label}. bar_with_color", bar_with_color, 0.5)
    index = label - 1
    start_x = bars_stats[index][0]
    end_x = start_x + bars_stats[index][2]

    start_y = bars_stats[index][1]
    end_y = start_y + bars_stats[index][3]

    bar_with_color_cropped = bar_with_color[start_y:end_y, start_x:end_x]

    image_rgb = bar_with_color_cropped
    pixels = image_rgb.reshape(-1, 3)
    unique_colors, counts = np.unique(pixels, axis=0, return_counts=True)
    unique_colors_with_counts = np.array(np.column_stack((unique_colors, counts)), np.uint32)
    unique_colors_with_counts = sorted(unique_colors_with_counts, key=lambda x: x[3], reverse=True)

    dominant_color = unique_colors_with_counts[0][:3].astype(np.uint8)[::-1]

    threshold = 100

    for i in range(1, len(unique_colors_with_counts)):
        vector_a = unique_colors_with_counts[i][:3].astype(np.uint8)

        dist = np.array(np.linalg.norm(vector_a - dominant_color), np.uint8)

        ratio = round(
            unique_colors_with_counts[i][3] / (bar_with_color_cropped.shape[0] * bar_with_color_cropped.shape[1]), 3)

        # at least the 50% of the bar has to be in the dominant color
        if dist <= threshold and ratio >= 0.5:
            dominant_color = np.array(np.average([dominant_color, vector_a], axis=0))[::-1]  # BGR -> RGB
            print(f"\nnew dominant color: {dominant_color}")
            # TODO check if works for 50% color

    return dominant_color


def scan_legend(legend):
    global legend_orig

    if legend is not None:
        legend_orig = legend.copy()
        bar_stats_with_colors = legend_detections.detect_legend_bars(legend)
        colors = merge_legend_bar_colors(bar_stats_with_colors)

        bars_max_x = 0

        for key, values in colors.items():
            bars_max_x = max(values["x"] + values["w"], bars_max_x)

        # print(bars_max_x)

        for key, values in colors.items():
            x = values["x"]
            y = values["y"]
            w = values["w"]
            h = values["h"]

            cv2.rectangle(legend_orig, (x, y), (x + w, y + h), (0, 0, 255), 2)
            # cv2.imshow("legend_orig", legend_orig)

        cv2.line(legend_orig, (bars_max_x, 0), (bars_max_x, legend_orig.shape[1]), (255, 0, 0), 2)
        # cv2.imshow("legend_orig", legend_orig)

        texts = legend_detections.detect_legend_texts(bars_max_x)
        bars_with_texts = legend_detections.merge_bars_with_texts(colors, texts)
        return bars_with_texts


def merge_legend_bar_colors(bar_stats_with_colors):
    # print(f"\tbar_stats_with_colors: {bar_stats_with_colors}")
    grouped_bgr_colors = {}
    threshold = 30
    similar_color_key = None

    for i, [pos, color] in enumerate(bar_stats_with_colors):
        # print(f"{i}. pos: {pos}, color: {color}")
        for key, values in grouped_bgr_colors.items():
            norm = int(np.linalg.norm(np.concatenate(cv2.subtract(values['color'], color, 1))))
            if norm <= threshold:
                similar_color_key = key
                break
            else:
                similar_color_key = None
            # print(f"norm: {values['color']} - {color} = {norm}, {key}")

        x = pos[0]
        y = pos[1]
        w = pos[2]
        h = pos[3]

        if similar_color_key is not None:
            min_x = min(grouped_bgr_colors[similar_color_key]["x"], x)
            min_y = min(grouped_bgr_colors[similar_color_key]["y"], y)
            max_w = max(grouped_bgr_colors[similar_color_key]["x"] + grouped_bgr_colors[similar_color_key]["w"],
                        x + w) - min_x
            max_h = max(grouped_bgr_colors[similar_color_key]["y"] + grouped_bgr_colors[similar_color_key]["h"],
                        y + h) - min_y

            grouped_bgr_colors[similar_color_key]["x"] = min_x
            grouped_bgr_colors[similar_color_key]["y"] = min_y
            grouped_bgr_colors[similar_color_key]["w"] = max_w
            grouped_bgr_colors[similar_color_key]["h"] = max_h

            average = np.array(np.average([grouped_bgr_colors[similar_color_key]['color'], color], axis=0), np.uint8)
            # print(f"{grouped_bgr_colors[similar_color_key]['color']} and {color} = {average}")
            grouped_bgr_colors[similar_color_key]["color"] = average

        else:
            grouped_bgr_colors[len(grouped_bgr_colors)] = {
                "color": color,
                "x": x,
                "y": y,
                "w": w,
                "h": h
            }

    print("\tgrouped_legend_bgr_colors: {\n\t\t" + "\n\t\t".join(
        f"{key}: {values}" for key, values in grouped_bgr_colors.items()) + "}")

    return grouped_bgr_colors


def merge_simple_chart_bar_colors(bar_stats_with_colors):
    global simple_chart_bar_color

    # print(f"\tbar_stats_with_colors: {bar_stats_with_colors}")
    grouped_bgr_colors = {}
    threshold = 30
    similar_color_key = None

    for i, [pos, color] in enumerate(bar_stats_with_colors):
        # print(f"{i}. pos: {pos}, color: {color}")
        for key, values in grouped_bgr_colors.items():
            norm = int(np.linalg.norm(np.concatenate(cv2.subtract(values['color'], color, 1))))
            if norm <= threshold:
                similar_color_key = key
                break
            else:
                similar_color_key = None
            # print(f"norm: {values['color']} - {color} = {norm}, {key}")

        if similar_color_key is not None:
            average = np.array(np.average([grouped_bgr_colors[similar_color_key]['color'], color], axis=0),
                               np.uint8)
            # print(f"{grouped_bgr_colors[similar_color_key]['color']} and {color} = {average}")
            simple_chart_bar_color = average

        else:
            simple_chart_bar_color = color

    print(f"\tsimple_chart_bar_color: {simple_chart_bar_color}")


def merge_grouped_chart_bar_colors(bar_stats_with_data):
    grouped_bars = {}
    threshold = 30
    similar_color_key = None

    for i, [pos, color] in enumerate(bar_stats_with_data):
        # print(f"{i}. pos: {pos}, color: {color}")
        for key, values in grouped_bars.items():
            norm = int(np.linalg.norm(np.concatenate(cv2.subtract(values['color'], color, 1))))
            if norm <= threshold:
                similar_color_key = key
                break
            else:
                similar_color_key = None
            # print(f"norm: {values['color']} - {color} = {norm}, {key}")

        x = pos[0]
        y = pos[1]
        w = pos[2]
        h = pos[3]

        # Similar color
        if similar_color_key is not None:
            grouped_bars[similar_color_key]["bars"].append({
                "x": x,
                "y": y,
                "w": w,
                "h": h
            })

            average = np.array(np.average([grouped_bars[similar_color_key]['color'], color], axis=0),
                               np.uint8)
            # print(f"{grouped_bgr_colors[similar_color_key]['color']} and {color} = {average}")
            grouped_bars[similar_color_key]["color"] = average

        # New color
        else:
            grouped_bars[len(grouped_bars)] = {
                "color": color,
                "bars": [
                    {
                        "x": x,
                        "y": y,
                        "w": w,
                        "h": h
                    }
                ]
            }

    print("\tgrouped_bars: {\n\t\t" + "\n\t\t".join(
        f"{key}: {values}" for key, values in grouped_bars.items()) + "}")

    return grouped_bars
