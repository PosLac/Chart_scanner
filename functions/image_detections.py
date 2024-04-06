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
sorted_y_axis_data = []
r_new_numbers = []
c_new_numbers = []
resized_gray = None
legend_orig = None
legend_without_bars = None
global_column_ticks_str = []
global_row_ticks_str = []
column_numbers_data = []
row_numbers_data = []
bars_with_axis_value_pairs = []
colors = None
title = None


def detect_title(title_pos, img):
    global title
    title_area = int(axis_detections.average_character_height * 3)

    if title_pos == 1:
        title_img = img[0:title_area, 0:]
    elif title_pos == -1:
        title_img = img[-title_area:, 0:]

    title_img = 255 - title_img
    _, labels, stats, _ = cv2.connectedComponentsWithStats(title_img, None, 8)

    sorted_stats = sorted(stats, key=lambda x: x[4], reverse=True)
    sorted_stats = np.delete(sorted_stats, 0, 0)
    threshold = round(axis_detections.average_character_height * 1.6, 3)
    sorted_stats = axis_detections.group_by_axis(sorted_stats, threshold, True)
    merged_stats = sorted_stats

    x_start = min(merged_stats, key=lambda x: x[0])[0]
    y_start = min(merged_stats, key=lambda x: x[1])[1]

    x_end = x_start + max(merged_stats, key=lambda x: x[2])[2]
    y_end = y_start + max(merged_stats, key=lambda x: x[3])[3]

    cropped_title_img = title_img[y_start:y_end, x_start:x_end]
    chart_title = pytesseract.pytesseract.image_to_string(cropped_title_img, config=config_title, lang='hun')
    print(f"\tDetected title: {chart_title}")
    title = chart_title

    title_stat = [x_start, x_end, y_start, y_end]
    if title_pos == -1:
        title_stat[2] = img.shape[0] - title_area + y_start
        title_stat[3] = img.shape[0] - title_area + y_end

    return chart_title, title_stat


def define_orientation():
    global elements, bar_hs, bars, ratios, r_numbers, orientation, resized_gray, r_numbers, c_numbers, mean
    resized = edits.resized_gray
    elements = edits.bars_stats
    bar_hs = []

    # Select biggest bar
    sorted_elements = sorted(elements, key=lambda x: x[4], reverse=True)
    max_full = sorted_elements[0]

    # Rendezés adott tengely szerint
    if max_full[3] > max_full[2]:
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
    # cv2.imwrite('rects_' + orientation + '.png', resized)
    # cv2.imwrite('bars_'+orientation+'.png', bars)

    print("Orientation done")


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


def define_simple_chart_values(bars_with_colors, y_axis_type, x_axis_type, y_axis_ticks, x_axis_ticks):
    global bar_hs, ratios, orientation, column_numbers_data, bars_with_axis_value_pairs

    text_for_axis = None

    if orientation == 'ybar':
        bars_with_colors = sorted(bars_with_colors, key=lambda x: x["x"])

    bars_with_colors = set_axis_value_for_bars(x_axis_type, x_axis_ticks, bars_with_colors, True, False)
    bars_with_colors = set_axis_value_for_bars(y_axis_type, y_axis_ticks, bars_with_colors, False, False)
    bars_with_axis_value_pairs = bars_with_colors

    print_array("bars_with_axis_value_pairs", bars_with_axis_value_pairs)

    if y_axis_type == "text":
        text_for_axis = y_axis_ticks

    elif x_axis_type == "text":
        text_for_axis = x_axis_ticks

    return text_for_axis


def define_grouped_chart_values(bars_with_colors, y_axis_type, x_axis_type, y_axis_ticks, x_axis_ticks):
    global bar_hs, orientation, ratios, bars_with_axis_value_pairs, colors

    text_for_axis = None

    if orientation == 'ybar':
        for group in bars_with_colors.values():
            group["bars"] = sorted(group["bars"], key=lambda x: x["x"])

    bars_with_colors = set_axis_value_for_bars(x_axis_type, x_axis_ticks, bars_with_colors, True, True)
    bars_with_colors = set_axis_value_for_bars(y_axis_type, y_axis_ticks, bars_with_colors, False, True)
    bars_with_axis_value_pairs = bars_with_colors

    print_array("bars_with_axis_value_pairs", bars_with_axis_value_pairs)

    if y_axis_type == "text":
        text_for_axis = y_axis_ticks

    elif x_axis_type == "text":
        text_for_axis = x_axis_ticks

    colors = {}
    for key, values in bars_with_axis_value_pairs.items():
        colors[key] = values["group_color"]

    return text_for_axis


def set_axis_value_for_bars(axis_type, tick_data_array, bar_data, for_x_axis, grouped):
    # Set indexes
    if for_x_axis:
        x_y_value_name = "x"
        w_h_value_name = "w"
        centoid_name = "centoid_x"
        value_name = "row value"
    else:
        x_y_value_name = "y"
        w_h_value_name = "h"
        centoid_name = "centoid_y"
        value_name = "column value"

    if grouped:
        if axis_type == "number":
            for values in bar_data.values():
                for bar in values["bars"]:
                    bar_value = axis_detections.find_value_of_bar(tick_data_array, bar, axis_type, for_x_axis, grouped)
                    bar[value_name] = bar_value
            return bar_data

        elif axis_type == "text":
            for values in bar_data.values():
                for bar in values["bars"]:
                    closest_tick_data = tick_data_array[0]

                    if for_x_axis:
                        bar_end = bar[x_y_value_name] + bar[w_h_value_name]
                    else:
                        bar_end = bar[x_y_value_name]

                    # Find the closest tick
                    for i, number_data in enumerate(tick_data_array):
                        if abs(bar_end - number_data[centoid_name]) <= abs(bar_end - closest_tick_data[centoid_name]):
                            closest_tick_data = number_data
                            value = axis_detections.find_value_of_bar(tick_data_array, bar, axis_type, for_x_axis,
                                                                      grouped)
                            bar[value_name] = value
            return bar_data

    else:
        if axis_type == "number":
            for bar in bar_data:
                value = axis_detections.find_value_of_bar(tick_data_array, bar, axis_type, for_x_axis, grouped)
                bar[value_name] = value
            return bar_data

        elif axis_type == "text":
            for bar in bar_data:
                closest_tick_data = tick_data_array[0]

                if for_x_axis:
                    bar_end = bar[x_y_value_name] + bar[w_h_value_name]
                else:
                    bar_end = bar[x_y_value_name]

                # Find the closest tick
                for i, number_data in enumerate(tick_data_array):
                    if abs(bar_end - number_data[centoid_name]) <= abs(bar_end - closest_tick_data[centoid_name]):
                        closest_tick_data = number_data
                        value = axis_detections.find_value_of_bar(tick_data_array, bar, axis_type, for_x_axis, grouped)
                        bar[value_name] = value
            return bar_data


def find_longest_bar(bars_with_data, horizontal):
    # Set indexes
    if horizontal:
        w_h_key = "w"
    else:
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

        for color in colors:
            x = color["x"]
            y = color["y"]
            w = color["w"]
            h = color["h"]

            cv2.rectangle(legend_for_draw, (x, y), (x + w, y + h), (0, 0, 255), 2)

        cv2.line(legend_for_draw, (bars_max_x, 0), (bars_max_x, legend_for_draw.shape[1]), (255, 0, 0), 2)

        legend_without_bars[:, :bars_max_x] = 255

        texts = legend_detections.detect_legend_texts(bars_max_x)
        bars_with_texts = legend_detections.merge_bars_with_texts(colors, texts)
        return bars_with_texts


# todo delete

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
