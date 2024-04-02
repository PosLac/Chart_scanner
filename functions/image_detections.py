import re

import cv2
import numpy as np
import pytesseract

import functions.legend_detections as legend_detections
import functions.image_edits as edits
from functions import color_detections, axis_detections

pytesseract.pytesseract.tesseract_cmd = 'D:/Apps/Tesseract/tesseract.exe'
# single_digit = r'--oem 3 --psm 10 -c tessedit_char_whitelist=0123456789'
single_digit = r'--oem 3 --psm 7 -c tessedit_char_whitelist=0123456789'
multi_digits = r'--oem 3 --psm 7 -c tessedit_char_whitelist=0123456789'
config_title = r'--oem 3 --psm 7'

chart_with_bars_img = None
ratios = None
new_numbers = None
orientation = None
chart_title = None
row_ticks_without_outliers = []
sorted_column_data = []
r_new_numbers = []
c_new_numbers = []
resized_gray = None
binary = None
legend_orig = None
legend_without_bars = None
average_character_height = None
global_column_ticks_str = []
global_row_ticks_str = []
column_numbers_data = []
row_numbers_data = []
bars_with_axis_value_pairs = []
colors = None


def connected_components():
    global orientation, binary, num_size, percent, resized_gray, chart_with_bars_img, r_numbers, centoids, stats, max_y, new_numbers, \
        chart_title, elements, x_bias, y_bias, col_nums, row_nums, \
        row_ticks_without_outliers, sorted_column_data, c_numbers_str, r_numbers_str, labels, average_character_height, global_row_ticks_str, global_column_ticks_str, row_numbers_data, column_numbers_data

    binary = edits.threshold()

    # number_of_components = background included
    # labels = matrix, 0-background, 1-component
    # stats = enclosing rectangle upper left point, width, length, number of pixels
    # centoids = center points of object
    number_of_components, labels, stats, centoids = cv2.connectedComponentsWithStats(binary, None, 8)

    isolated_column, isolated_row = axis_detections.isolate_x_y(binary.shape, number_of_components, stats)
    axis_detections.get_average_character_height(isolated_column)

    isolated_column = axis_detections.cut_column_outliers(isolated_column)
    isolated_row = axis_detections.cut_row_outliers(isolated_row)

    sorted_column_data = sorted(isolated_column, key=lambda x: (x[1], x[0]))
    sorted_row_data = sorted(isolated_row, key=lambda x: x[0])

    merged_row_data = axis_detections.merge_multi_digit_numbers(sorted_row_data, False)
    merged_column_data = axis_detections.merge_multi_digit_numbers(sorted_column_data, True)

    res = []
    big_res = []
    for stat in stats:
        if stat[4] < edits.NUM_SIZE:
            res.append(stat[2] * stat[3])
        else:
            big_res.append(stat)

    res_max = max(res) + 10
    chart_with_bars_img = binary.copy()

    # r_numbers = []
    # c_numbers = []
    for row_num in merged_row_data:
        # r_numbers.append(row_num)
        res.append(row_num)
        start = (row_num[0], row_num[1])
        end = (row_num[0] + row_num[2], row_num[1] + row_num[3])
        cv2.rectangle(edits.resized_gray, start, end, 0, 2)

    for col_num in merged_column_data:
        # c_numbers.append(col_num)
        res.append(col_num)
        start = (col_num[0], col_num[1])
        end = (col_num[0] + col_num[2], col_num[1] + col_num[3])
        cv2.rectangle(edits.resized_gray, start, end, 0, 3)

    i = 0
    percent = edits.UPSCALE_RATE
    x_bias = int(10 * percent)
    y_bias = int(9 * percent)

    x_bias = int(axis_detections.average_character_height // 2.7)
    y_bias = int(axis_detections.average_character_height // 3)

    _, labels, stats, centoids = cv2.connectedComponentsWithStats(binary, None, 8)
    sorted_stats = sorted(stats, key=lambda x: x[4], reverse=True)
    stats_max = sorted_stats[1]
    x1 = 0 if stats_max[0] < 0 else stats_max[0]
    x2 = x1 + stats_max[2]
    y1 = stats_max[1]
    y2 = y1 + stats_max[3]

    img_b = binary
    img_b[y1:y2, x1:x2] = 0
    img_b = axis_detections.remove_small_objects(sorted_stats, img_b)

    c_numbers_str = []
    for number in merged_column_data:
        x1 = 0 if number[0] - x_bias < 0 else number[0] - x_bias
        x2 = number[0] + number[2] + x_bias
        y1 = 0 if number[1] - y_bias < 0 else number[1] - y_bias
        y2 = number[1] + number[3] + y_bias

        img_re = img_b[y1:y2, x1:x2]
        img_re = 255 - img_re
        chart_with_bars_img[y1:y2 - y_bias, x1:x2 - x_bias] = 0

        title = pytesseract.pytesseract.image_to_string(img_re, config=multi_digits)
        title = re.sub(r'[\n]', '', title)
        cv2.imwrite(f"img_col{title}.png", img_re)
        c_numbers_str.append(title)
        i += 1

    r_numbers_str = []
    for number in merged_row_data:
        x1 = 0 if number[0] - x_bias < 0 else number[0] - x_bias
        x2 = number[0] + number[2] + x_bias
        y1 = 0 if number[1] - y_bias < 0 else number[1] - y_bias
        y2 = number[1] + number[3] + y_bias

        img_re = img_b[y1:y2, x1:x2]
        img_re = 255 - img_re
        chart_with_bars_img[y1:y2 - y_bias, x1:x2 - x_bias] = 0

        title = pytesseract.pytesseract.image_to_string(img_re, config=multi_digits)
        title = re.sub(r'[\n]', '', title)
        # cv2.imwrite(f"img_row {title}.png", img_re)
        r_numbers_str.append(title)
        i += 1

    # print('r_numbers_str: ', r_numbers_str)
    row_type = None
    row_type = 'str'
    row_type = 'int'
    col_type = None
    col_type = 'str'
    col_type = 'int'

    if row_type == 'int':
        global_row_ticks_str = axis_detections.convert_ticks_to_numbers(r_numbers_str)
        print_array("global_row_ticks_str", global_row_ticks_str)

        row_numbers_data = axis_detections.add_int_to_tick_data(global_row_ticks_str, merged_row_data)
        # print_array("row_numbers_data", row_numbers_data)
    # elif row_type == 'str':
    #     row_str()

    if col_type == 'int':
        global_column_ticks_str = axis_detections.convert_ticks_to_numbers(c_numbers_str)
        print_array("global_column_ticks_str", global_column_ticks_str)

        column_numbers_data = axis_detections.add_int_to_tick_data(global_column_ticks_str, merged_column_data)
        # print_array("column_numbers_data", column_numbers_data)

    elif col_type == 'str':
        axis_detections.col_str()


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
    global elements, bar_hs, bars, ratios, r_numbers, orientation, resized_gray, r_numbers, c_numbers, mean
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

    else:
        x_v = 2
        f_or_s = 1
        orientation = 'xbar'

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


def define_simple_chart_values(bars_with_colors):
    global bar_hs, ratios, orientation, r_new_numbers, c_new_numbers, row_numbers_data, column_numbers_data, bars_with_axis_value_pairs
    if orientation == 'xbar':
        longest_bar = max(bars_with_colors, key=lambda x: x["w"])
        ratios = np.round(bar_hs / longest_bar["w"], 2)
        axis_detections.tick_number_of_longest_bar = axis_detections.find_value_of_bar(row_numbers_data, longest_bar,
                                                                                       True)

        # if orientation == 'xbar':
        #     ratios = np.flip(ratios)

        bar_x_values = ratios * axis_detections.tick_number_of_longest_bar
        bars_with_colors = axis_detections.find_values_of_simple_bars(column_numbers_data, bars_with_colors, True)
        bars_with_axis_value_pairs = axis_detections.add_axis_value_pairs_to_bars(bar_x_values, bars_with_colors, False)

    elif orientation == 'ybar':
        bars_with_colors = sorted(bars_with_colors, key=lambda x: x["x"])

        longest_bar = max(bars_with_colors, key=lambda x: x["h"])
        ratios = np.round(bar_hs / longest_bar["h"], 2)

        axis_detections.tick_number_of_longest_bar = axis_detections.find_value_of_bar(column_numbers_data,
                                                                                       longest_bar, False)
        bar_x_values = ratios * axis_detections.tick_number_of_longest_bar
        bars_with_colors = axis_detections.find_values_of_simple_bars(row_numbers_data, bars_with_colors, False)
        bars_with_axis_value_pairs = axis_detections.add_axis_value_pairs_to_bars(bar_x_values,
                                                                                  bars_with_colors, False)


def define_grouped_chart_ratios(bars_with_data):
    global bar_hs, orientation, ratios, bars_with_axis_value_pairs, colors

    grouped_bars_with_data = bars_with_data
    # print_array("grouped_bars_with_data", grouped_bars_with_data)

    # if orientation == 'xbar':
    #     max_width = 0
    #
    #     # Find the longest bar
    #     for bar_group in bars_with_data.values():
    #         for bar in bar_group["bars"]:
    #             if bar["w"] > max_width:
    #                 max_width = bar["w"]
    #                 longest_bar = bar
    #
    #     # ratios = np.round(bar_hs / longest_bar["w"], 2)
    #
    #     longest_bar["row value"] = axis_detections.find_value_of_bar(row_numbers_data, longest_bar, True)
    #
    #     # longest_bar = find_longest_bar(bars_with_colors, True)
    #     # ratios = np.round(bar_hs / longest_bar["w"], 2)
    #     # bar_x_values = ratios * axis_detections.tick_number_of_longest_bar
    #
    #     bars_with_axis_value_pairs = axis_detections.find_values_of_grouped_bars(column_numbers_data, bars_with_data,
    #                                                                              longest_bar, True)
    #     # bars_with_axis_value_pairs = axis_detections.add_axis_value_pairs_to_bars(bar_x_values, bars_with_colors, True)
    #
    # elif orientation == 'ybar':
    #     max_height = 0
    #
    #     # Find the longest bar
    #     for bar_group in bars_with_data.values():
    #         for bar in bar_group["bars"]:
    #             if bar["h"] > max_height:
    #                 max_height = bar["h"]
    #                 longest_bar = bar
    #
    #     longest_bar["column value"] = axis_detections.find_value_of_bar(column_numbers_data, longest_bar, False)
    #     bars_with_axis_value_pairs = axis_detections.find_values_of_grouped_bars(row_numbers_data, bars_with_data,
    #                                                                              longest_bar, False)
    max_width_or_height = 0
    if orientation == "xbar":
        w_or_h_name = "w"
        row_or_column_value_name = "row value"
        numbers_data = row_numbers_data
        other_axis_numbers_data = column_numbers_data
    else:
        w_or_h_name = "h"
        row_or_column_value_name = "column value"
        numbers_data = column_numbers_data
        other_axis_numbers_data = row_numbers_data

    # Find the longest bar
    for bar_group in bars_with_data.values():
        for bar in bar_group["bars"]:
            if bar[w_or_h_name] > max_width_or_height:
                max_width_or_height = bar[w_or_h_name]
                longest_bar = bar

    longest_bar[row_or_column_value_name] = axis_detections.find_value_of_bar(numbers_data, longest_bar,
                                                                              orientation == "xbar")
    bars_with_axis_value_pairs = axis_detections.find_values_of_grouped_bars(other_axis_numbers_data, bars_with_data,
                                                                             longest_bar, orientation == "xbar")

    print_array("bars_with_axis_value_pairs", bars_with_axis_value_pairs)

    colors = {}
    for key, values in bars_with_axis_value_pairs.items():
        colors[key] = values["group_color"]


def find_longest_bar(bars_with_data, horizontal):
    # Set indexes
    if horizontal:
        x_y_key = "x"
        w_h_key = "w"
    else:
        x_y_key = "y"
        w_h_key = "h"

    # Find the longest bar
    longest_bar = max(bars_with_data, key=lambda x: x[w_h_key])

    print(f"longest_bar: {longest_bar}")
    return longest_bar


def scan_legend(legend):
    global legend_orig, legend_without_bars
    if legend is not None:
        legend_orig = legend.copy()
        legend_for_draw = legend.copy()
        legend_without_bars = legend.copy()

        legend_bar_stats_with_colors = legend_detections.detect_legend_bars(legend)
        print_array("legend_bar_stats_with_colors", legend_bar_stats_with_colors)

        colors = color_detections.merge_legend_bar_colors(legend_bar_stats_with_colors)
        print_array("colors", colors)

        bars_max_x = 0

        for color in colors:
            bars_max_x = max(color["x"] + color["w"], bars_max_x)

        # print(bars_max_x)

        for color in colors:
            x = color["x"]
            y = color["y"]
            w = color["w"]
            h = color["h"]

            cv2.rectangle(legend_for_draw, (x, y), (x + w, y + h), (0, 0, 255), 2)
            # cv2.imshow("legend_orig", legend_orig)

        cv2.line(legend_for_draw, (bars_max_x, 0), (bars_max_x, legend_for_draw.shape[1]), (255, 0, 0), 2)
        cv2.imwrite("legend_for_draw.png", legend_for_draw)

        legend_without_bars[:, :bars_max_x] = 255
        cv2.imwrite("legend_without_bars.png", legend_without_bars)

        texts = legend_detections.detect_legend_texts(bars_max_x)
        bars_with_texts = legend_detections.merge_bars_with_texts(colors, texts)
        return bars_with_texts


def print_array(name, array):
    if isinstance(array, list):
        print(f"\n\t{name}\n\t\t" + "\n\t\t".join(map(str, array)))

    elif isinstance(array, dict):
        print(f"\n\t{name}")

        for name, value in array.items():
            print(f"\t\t{name}:")

            for key, values in value.items():
                if key == "bars":
                    print(f"\t\t\t{key}:\n\t\t\t\t" + "\n\t\t\t\t".join(map(str, values)))
                else:
                    print(f"\t\t\t{key}:{values}")
