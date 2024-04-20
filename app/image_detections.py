import cv2
import numpy as np
import pytesseract

import app.image_edits as edits
import app.legend_detections as legend_detections
from app import color_detections, axis_detections
from config import config

logger = config.logger

pytesseract.pytesseract.tesseract_cmd = 'D:/Apps/Tesseract/tesseract.exe'
# single_digit = r'--oem 3 --psm 10 -c tessedit_char_whitelist=0123456789'
single_digit = r'--oem 3 --psm 7 -c tessedit_char_whitelist=0123456789'
multi_digits = r'--oem 3 --psm 7 -c tessedit_char_whitelist=0123456789'
config_title = r'--oem 3 --psm 10 -l hun+eng'

orientation = None
chart_title = None
legend_without_bars = None
bars_with_axis_value_pairs = []
colors = None
title = None
chart_type = None
text_for_axis = None


def detect_title(title_pos, img):
    global title, chart_title
    title_area = int(axis_detections.average_character_height * 2)
    _, _, all_stats, _ = cv2.connectedComponentsWithStats(img, None, 8)
    top_element = sorted(all_stats, key=lambda x: x[1])[1]

    if title_pos == 1:
        title_img = img[top_element[1]:top_element[1]+title_area, 0:]
    elif title_pos == -1:
        title_img = img[-title_area:, 0:]

    title_img = 255 - title_img
    _, _, stats, _ = cv2.connectedComponentsWithStats(title_img, None, 8)

    sorted_stats = sorted(stats, key=lambda x: x[4], reverse=True)
    sorted_stats = np.delete(sorted_stats, 0, 0)

    threshold = round(axis_detections.average_character_height * 1.6, 3)
    sorted_stats = axis_detections.group_by_axis(sorted_stats, threshold, True)
    merged_stats = sorted_stats

    x_start = max(0, min(merged_stats, key=lambda x: x[0])[0])
    y_start = max(0, min(merged_stats, key=lambda x: x[1])[1])

    x_end = min(title_img.shape[1], x_start + max(merged_stats, key=lambda x: x[2])[2])
    y_end = min(title_img.shape[0], y_start + max(merged_stats, key=lambda x: x[3])[3])

    cropped_title_img = title_img[y_start:y_end, x_start:x_end]
    # cv2.imwrite("A-cropped_title_img.png", cropped_title_img)
    chart_title = pytesseract.pytesseract.image_to_string(cropped_title_img, config=config_title, lang='hun')
    logger.info(f"Detected title: {chart_title}")
    title = chart_title

    title_stat = [x_start, x_end, y_start, y_end]
    if title_pos == -1:
        title_stat[2] = img.shape[0] - title_area + y_start
        title_stat[3] = img.shape[0] - title_area + y_end

    return chart_title, title_stat


def define_orientation():
    global orientation
    elements = edits.bars_stats

    # Select biggest bar
    sorted_elements = sorted(elements, key=lambda x: x[4], reverse=True)
    max_full = sorted_elements[0]

    # Rendezés adott tengely szerint
    if max_full[3] > max_full[2]:
        orientation = 'ybar'

    else:
        orientation = 'xbar'

    logger.info(f"{'Horizontal' if orientation == 'xbar' else 'Vertical'} chart detected")


def define_simple_chart_values(bars_with_colors):
    global orientation, bars_with_axis_value_pairs, text_for_axis

    axis_types_with_ticks = axis_detections.axis_types_with_ticks
    if orientation == 'ybar':
        bars_with_colors = sorted(bars_with_colors, key=lambda x: x["x"])

    bars_with_colors = set_axis_value_for_bars(axis_types_with_ticks["x_axis_type"],
                                               axis_types_with_ticks["x_axis_ticks"], bars_with_colors, True, False)
    bars_with_colors = set_axis_value_for_bars(axis_types_with_ticks["y_axis_type"],
                                               axis_types_with_ticks["y_axis_ticks"], bars_with_colors, False, False)
    bars_with_axis_value_pairs = bars_with_colors

    # print_array("bars_with_axis_value_pairs", bars_with_axis_value_pairs)

    text_for_axis = None
    if axis_types_with_ticks["y_axis_type"] == "text":
        text_for_axis = axis_types_with_ticks["y_axis_ticks"]

    elif axis_types_with_ticks["x_axis_type"] == "text":
        text_for_axis = axis_types_with_ticks["x_axis_ticks"]


def define_grouped_chart_values(bars_with_colors):
    global orientation, bars_with_axis_value_pairs, colors, text_for_axis

    if orientation == 'ybar':
        for group in bars_with_colors.values():
            group["bars"] = sorted(group["bars"], key=lambda x: x["x"])
    axis_types_with_ticks = axis_detections.axis_types_with_ticks
    bars_with_colors = set_axis_value_for_bars(axis_types_with_ticks["x_axis_type"],
                                               axis_types_with_ticks["x_axis_ticks"], bars_with_colors, True, True)
    bars_with_colors = set_axis_value_for_bars(axis_types_with_ticks["y_axis_type"],
                                               axis_types_with_ticks["y_axis_ticks"], bars_with_colors, False, True)
    bars_with_axis_value_pairs = bars_with_colors

    # print_array("bars_with_axis_value_pairs", bars_with_axis_value_pairs)

    text_for_axis = None
    if axis_types_with_ticks["y_axis_type"] == "text":
        text_for_axis = axis_types_with_ticks["y_axis_ticks"]

    elif axis_types_with_ticks["x_axis_type"] == "text":
        text_for_axis = axis_types_with_ticks["x_axis_ticks"]

    colors = {}
    for key, values in bars_with_axis_value_pairs.items():
        colors[key] = values["group_color"]


def define_stacked_chart_values(bars_with_colors_dict):
    global orientation, bars_with_axis_value_pairs, colors, text_for_axis

    axis_types_with_ticks = axis_detections.axis_types_with_ticks

    if orientation == "xbar":
        other_x_y_name = "y"
        other_w_h_name = "h"

    elif orientation == "ybar":
        other_x_y_name = "x"
        other_w_h_name = "w"

    for group in bars_with_colors_dict.values():
        group["bars"] = sorted(group["bars"], key=lambda x: x[other_x_y_name])

    bars_with_colors_dict = set_axis_value_for_bars(axis_types_with_ticks["x_axis_type"],
                                                    axis_types_with_ticks["x_axis_ticks"], bars_with_colors_dict, True,
                                                    True)
    bars_with_colors_dict = set_axis_value_for_bars(axis_types_with_ticks["y_axis_type"],
                                                    axis_types_with_ticks["y_axis_ticks"], bars_with_colors_dict, False,
                                                    True)

    bars_with_colors = []
    for key, value in bars_with_colors_dict.items():
        for bar in value["bars"]:
            bar["group"] = key
            bars_with_colors.append(bar)

    bars_with_colors = sorted(bars_with_colors, key=lambda x: x[other_x_y_name])
    # print_array("bars_with_colors", bars_with_colors)

    grouped_bars = [[bars_with_colors[0]]]
    threshold = 10

    # Group bars by ticks to a list
    for bar in bars_with_colors[1:]:
        i_centoid = bar[other_x_y_name] + bar[other_w_h_name] // 2
        j_centoid = grouped_bars[-1][-1][other_x_y_name] + grouped_bars[-1][-1][other_w_h_name] // 2

        if abs(i_centoid - j_centoid) <= threshold:
            grouped_bars[-1].append(bar)
        else:
            grouped_bars.append([bar])

    bars_with_colors_dict = set_ticks(grouped_bars, bars_with_colors_dict, axis_types_with_ticks["y_axis_type"],
                                      axis_types_with_ticks["y_axis_ticks"], False)
    bars_with_colors_dict = set_ticks(grouped_bars, bars_with_colors_dict, axis_types_with_ticks["x_axis_type"],
                                      axis_types_with_ticks["x_axis_ticks"], True)

    bars_with_axis_value_pairs = bars_with_colors_dict

    colors = {}
    for key, values in bars_with_axis_value_pairs.items():
        colors[key] = values["group_color"]

    text_for_axis = None
    if axis_types_with_ticks["y_axis_type"] == "text":
        text_for_axis = axis_types_with_ticks["y_axis_ticks"]

    elif axis_types_with_ticks["x_axis_type"] == "text":
        text_for_axis = axis_types_with_ticks["x_axis_ticks"]


def set_ticks(grouped_bars, bars_with_colors_dict, axis_type, axis_ticks, x_axis):
    if x_axis:
        x_y_name = "x"
        w_h_name = "w"
        value_name = "row value"

    else:
        x_y_name = "y"
        w_h_name = "h"
        value_name = "column value"

    if axis_type == "number":
        for group in grouped_bars:
            bar_start = min(group, key=lambda x: x[x_y_name])
            bar_end = max(group, key=lambda x: x[x_y_name] + x[w_h_name])
            bar_length = bar_end[x_y_name] + bar_end[w_h_name] - bar_start[x_y_name]

            for bar in group:
                bar["percent"] = round(bar[w_h_name] / bar_length, 3)

            if x_axis:
                max_bar = bar_end
            else:
                max_bar = bar_start

            value = axis_detections.find_value_of_bar(axis_ticks, max_bar, axis_type, x_y_name == "x", False)
            max_bar[value_name] = value

            for bar in group:
                bar[value_name] = round(bar["percent"] * max_bar[value_name], 2)

    return bars_with_colors_dict


def detect_if_chart_is_stacked(grouped_bars_by_ticks):
    global chart_type
    bar_list = []

    # Extract bars to a list
    for values in grouped_bars_by_ticks.values():
        bar_list.extend(values["bars"])

    if orientation == "xbar":
        x_y_name = "y"
        w_h_name = "h"

    elif orientation == "ybar":
        x_y_name = "x"
        w_h_name = "w"

    bar_list = sorted(bar_list, key=lambda x: x[x_y_name])

    grouped_bars = [[bar_list[0]]]
    threshold = 10
    groups = 0

    # Group bars by ticks to a list
    for bar in bar_list[1:]:
        i_centoid_x = bar[x_y_name] + bar[w_h_name] // 2
        j_centoid_x = grouped_bars[-1][-1][x_y_name] + grouped_bars[-1][-1][w_h_name] // 2

        if abs(i_centoid_x - j_centoid_x) <= threshold:
            grouped_bars[-1].append(bar)
            groups += 1
        else:
            grouped_bars.append([bar])

    stacked = False

    if groups > 1:
        stacked = True

    return stacked


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
                    value = axis_detections.find_value_of_bar(tick_data_array, bar, axis_type, for_x_axis, grouped)
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

    return longest_bar


def scan_legend(legend):
    global legend_without_bars
    if legend is not None:
        legend_without_bars = legend.copy()

        legend_bar_stats_with_colors = legend_detections.detect_legend_bars(legend)
        # print_array("legend_bar_stats_with_colors", legend_bar_stats_with_colors)

        colors = color_detections.merge_legend_bar_colors(legend_bar_stats_with_colors)
        # print_array("colors", colors)

        bars_max_x = 0

        for color in colors:
            bars_max_x = max(color["x"] + color["w"], bars_max_x)

        legend_without_bars[:, :bars_max_x] = 255

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
