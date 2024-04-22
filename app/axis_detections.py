import cv2
import numpy as np
import pytesseract

import app.image_edits as edits
from app import image_detections
from config import config

THRESHOLD = 230

average_character_height = None
longest_bar_value = None
config_title = r'--oem 3 --psm 10 -l hun+eng'
axis_types_with_ticks = {}
logger = config.logger


def remove_title_from_img(binary, title_stats):
    start_x = title_stats[0]
    end_x = min(title_stats[1], binary.shape[0])

    start_y = title_stats[2]
    end_y = min(title_stats[3], binary.shape[1])

    binary[start_y:end_y, start_x:end_x] = 0
    return binary


def remove_bars_from_img(binary):
    _, _, stats, _ = cv2.connectedComponentsWithStats(binary, None, 8)
    sorted_stats = sorted(stats, key=lambda x: x[4], reverse=True)
    stats_max = sorted_stats[1]
    x1 = 0 if stats_max[0] < 0 else stats_max[0]
    x2 = x1 + stats_max[2]
    y1 = stats_max[1]
    y2 = y1 + stats_max[3]

    ticks_img = binary.copy()
    ticks_img[y1:y2, x1:x2] = 0
    return ticks_img


def define_tick_type_for_axis(title_pos):
    global average_character_height, axis_types_with_ticks

    binary_orig = edits.thresholding(THRESHOLD)
    only_ticks_img = remove_bars_from_img(binary_orig)
    _, _, stats, _ = cv2.connectedComponentsWithStats(only_ticks_img, None, 8)

    # Remove background
    stats = np.delete(stats, 0, 0)
    image_detections.define_orientation()
    isolated_y_axis, isolated_x_axis = isolate_x_y(stats)
    get_average_character_height(isolated_y_axis)
    image_detections.chart_title = None

    if title_pos:
        image_detections.chart_title, title_stats = image_detections.detect_title(title_pos, only_ticks_img)
        only_ticks_img = remove_title_from_img(only_ticks_img, title_stats)
        if title_pos == -1:
            _, _, stats, _ = cv2.connectedComponentsWithStats(only_ticks_img, None, 8)
            stats = np.delete(stats, 0, 0)
            isolated_y_axis, isolated_x_axis = isolate_x_y(stats)
            get_average_character_height(isolated_y_axis)

    isolated_x_axis = cut_row_outliers(isolated_x_axis)

    threshold = round(average_character_height * 1.6, 3)
    sorted_y_axis_data = group_by_axis(isolated_y_axis, threshold, False)
    merged_y_axis_ticks = merge_tick_characters(sorted_y_axis_data, threshold)

    sorted_x_axis_data = group_by_axis(isolated_x_axis, threshold, True)
    threshold = round(average_character_height * 0.6, 3)
    merged_x_axis_ticks = merge_tick_characters(sorted_x_axis_data, threshold)

    y_axis_type, corrected_y_axis_ticks = define_axis_type(merged_y_axis_ticks, merged_x_axis_ticks, only_ticks_img)
    logger.info(f"Y axis ticks after correction: {corrected_y_axis_ticks}")
    logger.info(f"Y axis type: {y_axis_type}")

    x_axis_type, corrected_x_axis_ticks = define_axis_type(merged_x_axis_ticks, merged_y_axis_ticks, only_ticks_img)
    logger.info(f"X axis ticks after correction: {corrected_x_axis_ticks}")
    logger.info(f"X axis type: {x_axis_type}")

    y_axis_data = add_value_to_tick_data(corrected_y_axis_ticks, merged_y_axis_ticks)
    x_axis_data = add_value_to_tick_data(corrected_x_axis_ticks, merged_x_axis_ticks)

    axis_types_with_ticks = {
        "y_axis_type": y_axis_type,
        "y_axis_ticks": y_axis_data,
        "y_axis_max": corrected_y_axis_ticks[0],
        "y_axis_min": corrected_y_axis_ticks[-1],
        "x_axis_type": x_axis_type,
        "x_axis_ticks": x_axis_data,
        "x_axis_max": corrected_x_axis_ticks[-1],
        "x_axis_min": corrected_x_axis_ticks[0],
    }


def define_axis_type(merged_ticks, merged_ticks_of_other_axis, only_ticks_img_orig):
    global average_character_height, config_title

    max_y = only_ticks_img_orig.shape[0]
    max_x = only_ticks_img_orig.shape[1]
    bias = int(average_character_height * 0.5)
    ticks_str_array = []
    only_ticks_img_copy = only_ticks_img_orig.copy()

    for tick_data in merged_ticks_of_other_axis:
        start_y = tick_data[1]
        end_y = tick_data[1] + tick_data[3]

        start_x = tick_data[0]
        end_x = tick_data[0] + tick_data[2]
        only_ticks_img_copy[start_y:end_y, start_x:end_x] = 0

    for tick_data in merged_ticks:
        start_y = max(tick_data[1] - bias, 0)
        end_y = min(tick_data[1] + tick_data[3] + bias, max_y)

        start_x = max(tick_data[0] - bias, 0)
        end_x = min(tick_data[0] + tick_data[2] + bias, max_x)

        cropped_tick_img = only_ticks_img_copy[start_y:end_y, start_x:end_x]
        tick_str = pytesseract.pytesseract.image_to_string(cropped_tick_img, config=config_title)
        ticks_str_array.append(tick_str.strip())

    tick_number_array = []
    tick_number = 0
    for tick_str in ticks_str_array:
        char_digit = 0
        tick_without_comma = tick_str.replace(",", "")
        for character in tick_without_comma:
            if character.isdigit():
                char_digit += 1

        if char_digit >= len(tick_without_comma) * 0.8:
            tick_number += 1
            tick_number_array.append(tick_without_comma)
        else:
            tick_number_array.append(tick_str)

    if tick_number >= len(ticks_str_array) * 0.5:
        ticks_type = "number"
        logger.info(f"Tick numbers before correction: {tick_number_array}")
        corrected_ticks = correcting_steps_between_ticks(tick_number_array)
        return ticks_type, corrected_ticks
    else:
        ticks_type = "text"
        return ticks_type, tick_number_array


def group_by_axis(tick_data, threshold, horizontal):
    groups = {}

    if horizontal:
        first_group_index = 0
        tick_data = sorted(tick_data, key=lambda x: x[0])
    else:
        first_group_index = 1

    for item in tick_data:
        group_key = round(item[first_group_index] / threshold, 2)
        added = False
        for key, value in groups.items():
            if abs(key - group_key) <= 1:
                groups[key].append(item)
                added = True

        if not added:
            groups[group_key] = [item]

    sorted_data = []
    for group in sorted(groups.keys()):
        sorted_group = sorted(groups[group], key=lambda x: x[0])
        sorted_data.extend(sorted_group)

    return sorted_data


def merge_tick_characters(sorted_data, threshold):
    temp_numbers = []

    for i in range(len(sorted_data)):
        # Check if not component of a multi digit number
        if len(sorted_data[i]) > 1:
            i_x = sorted_data[i][0]
            i_y = sorted_data[i][1]
            i_w = sorted_data[i][2]
            i_h = sorted_data[i][3]
            i_pixels = sorted_data[i][4]
            i_centoid_y = i_y + i_h / 2

            multi_digit_number = []

            for j in range(i + 1, len(sorted_data)):
                # Check if not component of a multi digit number
                if len(sorted_data[j]) > 1:
                    j_x = sorted_data[j][0]
                    j_y = sorted_data[j][1]
                    j_w = sorted_data[j][2]
                    j_h = sorted_data[j][3]
                    j_pixels = sorted_data[j][4]
                    j_centoid_y = j_y + j_h / 2

                    # Break if number is from another column tick
                    if abs(i_centoid_y - j_centoid_y) >= threshold:
                        break

                    # If end of number is close to another number
                    if abs((i_x + i_w) - j_x) <= threshold or abs((i_y + i_h) - j_y) <= threshold:
                        # Set empty array for multi digit number parts
                        sorted_data[i] = [0]
                        sorted_data[j] = [0]
                        # Add multi digit number
                        min_y = min(i_y, j_y)
                        max_height = max(i_y + i_h, j_y + j_h)
                        multi_digit_number = [i_x, min_y, j_x + j_w - i_x, max_height - min_y,
                                              i_pixels + j_pixels]

                        i_x = multi_digit_number[0]
                        i_y = multi_digit_number[1]
                        i_w = multi_digit_number[2]
                        i_h = multi_digit_number[3]
                        i_pixels = multi_digit_number[4]

            # Check if still not component of a multi digit number
            if len(sorted_data[i]) > 1:
                temp_numbers.append(sorted_data[i])
            else:
                temp_numbers.append(multi_digit_number)
    return temp_numbers


def isolate_x_y(stats):
    col_nums = []
    row_nums = []

    # Searching in the left-side for y-axis and bottom for x-axis of the picture
    left_x_for_column = min(edits.bars_stats[:, 0])

    start_of_bars = max(edits.bars_stats, key=lambda x: x[1] + x[3])
    upper_y_for_row = start_of_bars[1] + start_of_bars[3]

    if image_detections.orientation == "xbar":
        for stat in stats:
            x_end = stat[0] + stat[2]
            y_start = stat[1]

            if x_end < left_x_for_column:
                col_nums.append(stat)

            elif y_start > upper_y_for_row:
                row_nums.append(stat)

    elif image_detections.orientation == "ybar":

        for stat in stats:
            x_end = stat[0] + stat[2]
            y_start = stat[1]

            if y_start > upper_y_for_row:
                row_nums.append(stat)

            elif x_end < left_x_for_column:
                col_nums.append(stat)

    return col_nums, row_nums


def get_average_character_height(col_nums):
    global average_character_height

    average_character_height = int(np.mean(np.array(col_nums)[:, 3]))
    logger.info(f"Detected average character height: {average_character_height}")


def find_value_of_bar(tick_data_array, bar_object, axis_type, horizontal, grouped):
    # Set indexes
    if horizontal:
        x_y_value_name = "x"
        w_h_value_name = "w"
        centoid_name = "centoid_x"
    else:
        x_y_value_name = "y"
        w_h_value_name = "h"
        centoid_name = "centoid_y"

    closest_tick_data = tick_data_array[0]

    if horizontal:
        bar_end = bar_object[x_y_value_name] + bar_object[w_h_value_name]
    else:
        bar_end = bar_object[x_y_value_name]

    # Find the closest tick
    for i, number_data in enumerate(tick_data_array):
        if abs(bar_end - number_data[centoid_name]) <= abs(bar_end - closest_tick_data[centoid_name]):
            closest_tick_data = number_data

    if axis_type == "text" or (grouped and (image_detections.orientation == "xbar") != horizontal):
        return closest_tick_data["value"]

    elif axis_type == "number":
        distance_from_closest_tick = bar_end - closest_tick_data[centoid_name]

        if distance_from_closest_tick == 0:
            value_of_bar = int(closest_tick_data["value"])
            return value_of_bar

        average_tick_distance = calculate_average_tick_distance(tick_data_array, horizontal)
        average_tick_step = calculate_average_tick_step(tick_data_array, False)

        value_of_bar = int(closest_tick_data["value"]) + round(
            distance_from_closest_tick / average_tick_distance * average_tick_step, 2)

        return value_of_bar


def calculate_average_tick_distance(tick_data, horizontal):
    centoids = []

    # Set indexes

    centoid_name = "centoid_x" if horizontal else "centoid_y"

    for tick in tick_data:
        centoids.append(tick[centoid_name])

    average_tick_distance = int(np.std(centoids))
    return average_tick_distance


def calculate_average_tick_step(tick_data, for_str_array):
    values = []

    if for_str_array:
        values = tick_data
    else:
        for tick in tick_data:
            values.append(int(tick["value"]))

    steps = []
    for i in range(len(values) - 1):
        if values[i] != "" and values[i + 1] != "":
            steps.append(values[i + 1] - values[i])

    if len(steps) == 0:
        raise Exception("Can't calculate the step values") #TODO magyar hibaüzenet
    unique_steps, counts = np.unique(steps, axis=0, return_counts=True)

    corrected_step = [x for _, x in sorted(zip(counts, unique_steps), reverse=True)][0]

    return corrected_step


def cut_column_outliers(isolated_column):
    global average_character_height

    centoid_distances = average_character_height * 3

    while centoid_distances >= average_character_height:

        x_of_centoids = []

        for num in isolated_column:
            num_centoid_x = int((num[0] + num[2]) / 2)
            x_of_centoids.append(num_centoid_x)

        average_centoid = np.mean(np.array(x_of_centoids))

        centoid_distances = np.std(x_of_centoids)

        c_final = []
        for num in isolated_column:
            centoid_x = int((num[0] + num[2]) / 2)

            if abs(centoid_x - average_centoid) < centoid_distances or abs(
                    centoid_x - average_centoid) < average_character_height:
                c_final.append(num)
        isolated_column = c_final

    return isolated_column


def cut_row_outliers(isolated_row):
    j = 0
    std_r = 100

    while std_r > 10 and j < len(isolated_row):
        sum_r = 0
        for r in isolated_row:
            sum_r += r[1]

        mean_r = sum_r / len(isolated_row)

        row_ticks_without_outliers = []
        r_y = []
        for y in isolated_row:
            r_y.append(y[1])

        std_r = np.std(r_y)
        for r in isolated_row:
            if abs(r[1] - mean_r) < std_r or std_r < 5:
                row_ticks_without_outliers.append(r)
        isolated_row = row_ticks_without_outliers

        j += 1
    return isolated_row


def merge_multi_digit_numbers(numbers, column):
    global average_character_height
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

                        numbers[i] = [0]
                        numbers[j] = [0]
                        # Add multi digit number
                        multi_digit_number = [i_x, i_y, j_x + j_w - i_x, i_h, i_pixels + j_pixels]

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


def remove_small_objects(sorted_stats, img_b):
    global average_character_height
    # Delete commas and small objects
    for stat in sorted_stats:
        if stat[2] < average_character_height * 0.7 and stat[3] < average_character_height * 0.7:
            x1 = stat[0]
            x2 = x1 + stat[2]
            y1 = stat[1]
            y2 = y1 + stat[3]
            img_b[y1:y2, x1:x2] = 0

    return img_b


def correcting_steps_between_ticks(numbers_str_array):
    # Insert missing tick and convert str to int
    for i in range(len(numbers_str_array)):
        try:
            numbers_str_array[i] = int(numbers_str_array[i])
        except ValueError:
            numbers_str_array[i] = ""
            logger.info("Can't convert non-number tick to number, replaced with empty str")

    average_step = calculate_average_tick_step(numbers_str_array, True)
    wrong_step_indexes = []

    # Save indexes between two values with wrong step
    for i in range(1, len(numbers_str_array)):
        if numbers_str_array[i] == "":
            wrong_step_indexes.append(i - 1)

        elif numbers_str_array[i - 1] == "":
            wrong_step_indexes.append(i - 1)

        elif abs(numbers_str_array[i - 1] + average_step - numbers_str_array[i]) > 0:
            wrong_step_indexes.append(i - 1)
            numbers_str_array[i] = ""

    # index 0    1    2      3      4      5      6
    # value 55   1000   1500   2000   2500   3000
    # step     0      1      2      3      4

    # Fix wrong values
    for wrong_step in wrong_step_indexes:

        if wrong_step == 0:
            for i in range(wrong_step, len(numbers_str_array)):
                if i + 1 not in wrong_step_indexes and i + 1 < len(numbers_str_array) - 2:
                    numbers_str_array[wrong_step] = numbers_str_array[i + 1] - (average_step * (i + 1))

        # Last step is wrong
        elif wrong_step == len(numbers_str_array) - 2:

            # Tick before last is wrong
            if numbers_str_array[wrong_step] == "":
                numbers_str_array[wrong_step] = numbers_str_array[wrong_step - 1] + average_step

            # Last tick is wrong
            if numbers_str_array[-1] == "":
                numbers_str_array[-1] = numbers_str_array[wrong_step] + average_step
        else:
            numbers_str_array[wrong_step] = numbers_str_array[wrong_step - 1] + average_step

    return numbers_str_array


def convert_ticks_to_numbers(numbers_str_array):
    # Remove whitespaces
    for i in range(len(numbers_str_array)):
        splitted_number = numbers_str_array[i].split()
        numbers_str_array[i] = ''.join(splitted_number)

    return correcting_steps_between_ticks(numbers_str_array)


def add_value_to_tick_data(numbers_str_array, numbers_data):
    global average_character_height
    j = 0
    new_numbers = []
    x_bias = int(average_character_height // 2.7)
    y_bias = int(average_character_height // 3)

    for number in numbers_data:
        x2 = number[0] + number[2] + x_bias
        y2 = number[1] + number[3] + y_bias
        # cv2.putText(edits.resized_gray, str(numbers_str_array[j]), (x2 - x_bias, y2), cv2.QT_FONT_NORMAL, 1, 0, 2)
        centoid_x = np.round(number[0] + (number[2] // 2))
        centoid_y = np.round(number[1] + (number[3] // 2))
        new_number = {
            "x": number[0],
            "y": number[1],
            "w": number[2],
            "h": number[3],
            "centoid_x": centoid_x,
            "centoid_y": centoid_y,
            "value": numbers_str_array[j],
        }
        new_numbers.append(new_number)
        j += 1

    return new_numbers


def add_axis_value_pairs_to_bars(bar_x_values, bar_data, grouped):
    if grouped:
        for group in bar_data.values():
            for i in range(len(group["bars"])):
                group["bars"][i]["row value"] = round(bar_x_values[i], 2)

    else:
        for i in range(len(bar_data)):
            bar_data[i]["row value"] = round(bar_x_values[i], 2)

    # image_detections.print_array("bar_data", bar_data)

    return bar_data


def find_values_of_grouped_bars(ticks_data, bar_data, longest_bar, horizontal):
    closest_tick_data = ticks_data[0]
    centoid_name = "centoid_y" if horizontal else "centoid_x"
    bar_x_y_name = "y" if horizontal else "x"
    bar_w_h_name = "h" if horizontal else "w"
    other_bar_w_h_name = "w" if horizontal else "h"
    bar_value_name = "column value" if horizontal else "row value"
    other_bar_value_name = "row value" if horizontal else "column value"

    for group in bar_data.values():
        for i, bar in enumerate(group["bars"]):
            bar_centoid = bar[bar_x_y_name] + (bar[bar_w_h_name] // 2)

            # Find the closest tick
            for tick in ticks_data:
                if abs(bar_centoid - tick[centoid_name]) <= abs(bar_centoid - closest_tick_data[centoid_name]):
                    closest_tick_data = tick

            group["bars"][i][bar_value_name] = closest_tick_data["value"]
            group["bars"][i][other_bar_value_name] = round(
                longest_bar[other_bar_value_name] * (bar[other_bar_w_h_name] / longest_bar[other_bar_w_h_name]), 2)

            # # Find vertical distance between bar and closest tick
            # distance_from_closest_tick = abs(bar_centoid - closest_tick_data[centoid_name])
            #
            # # Calculate the value of the bar on the vertical axis
            # if distance_from_closest_tick == 0:
            #     tick_value_of_bar = closest_tick_data["value"]
            #
            # else:
            #
            #     # Bar is under the closest tick
            #     if bar_centoid > closest_tick_data[centoid_name]:
            #         tick_value_of_bar = closest_tick_data["value"] - (
            #                 distance_from_closest_tick / average_tick_distance * abs(average_tick_step))
            #
            #     # Bar is above the closest tick
            #     else:
            #         tick_value_of_bar = closest_tick_data["value"] + (
            #                 distance_from_closest_tick / average_tick_distance * abs(average_tick_step))
            #
            # group["bars"][i][bar_value_name] = round(tick_value_of_bar, 2)
            # group["bars"][i][other_bar_value_name] = round(
            #     longest_bar[other_bar_value_name] * (bar[other_bar_w_h_name] / longest_bar[other_bar_w_h_name]), 2)
    return bar_data


def find_values_of_simple_bars(ticks_data, bar_data, horizontal):
    average_tick_step = calculate_average_tick_step(ticks_data, False)
    average_tick_distance = calculate_average_tick_distance(ticks_data, not horizontal)
    closest_tick_data = ticks_data[0]
    centoid_name = "centoid_y" if horizontal else "centoid_x"
    bar_x_y_name = "y" if horizontal else "x"
    bar_w_h_name = "h" if horizontal else "w"

    for i, bar in enumerate(bar_data):
        bar_centoid = bar[bar_x_y_name] + (bar[bar_w_h_name] // 2)

        # Find the closest tick
        for tick in ticks_data:

            if abs(bar_centoid - tick[centoid_name]) <= abs(bar_centoid - closest_tick_data[centoid_name]):
                closest_tick_data = tick

        # Find vertical distance between bar and closest tick
        distance_from_closest_tick = abs(bar_centoid - closest_tick_data[centoid_name])

        # Calculate the value of the bar on the vertical axis
        if distance_from_closest_tick == 0:
            tick_value_of_bar = closest_tick_data["value"]

        else:

            # Bar is under the closest tick
            if bar_centoid > closest_tick_data[centoid_name]:
                tick_value_of_bar = round(closest_tick_data["value"] - (
                        distance_from_closest_tick / average_tick_distance * abs(average_tick_step)), 2)

            # Bar is above the closest tick
            else:
                tick_value_of_bar = round(closest_tick_data["value"] + (
                        distance_from_closest_tick / average_tick_distance * abs(average_tick_step)), 2)

        bar_data[i]["column value"] = round(tick_value_of_bar, 2)

    return bar_data
