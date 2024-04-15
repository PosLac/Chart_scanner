import cv2
import numpy as np

from functions import image_detections, image_edits

similar_color_threshold = 40


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
    bars_img = np.ndarray(img.shape)
    # print(f"bar_stats: {bar_stats}")
    for i in range(len(bar_stats)):
        bars_img.fill(0)
        color_bgr = detect_bar_color(img, bar_stats, bars_labels, i + 1)
        bars_with_colors.append({
            "x": bar_stats[i][0],
            "y": bar_stats[i][1],
            "w": bar_stats[i][2],
            "h": bar_stats[i][3],
            "bgr_color": np.array(color_bgr)
        })
        # print(f"{i}. (stats: {bar_stats[i]}) \t (color: {color_rgb})")
        bars_img[bars_labels == i + 1] = 255
    # image_detections.print_array("bars_with_colors", bars_with_colors)
    return bars_with_colors


def detect_bars_by_color(all_color_bars_img, color):
    cv2.imwrite("A-all_color_bars_img.png", all_color_bars_img)
    bars_with_stats = []

    norm = np.array(np.clip(np.linalg.norm(all_color_bars_img - color, axis=-1), 0, 255), np.uint8)
    cv2.imwrite("A-norm.png", norm)

    retval = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    norm = cv2.dilate(norm, retval, None, None, 1)
    norm = cv2.erode(norm, retval, None, None, 2)
    norm = cv2.dilate(norm, retval, None, None, 1)
    cv2.imwrite("A-norm2.png", norm)

    color_mask = np.array(norm < similar_color_threshold, np.uint8)
    color_mask[color_mask > 0] = 255
    color_mask = 255 - color_mask
    cv2.imwrite("A-color_mask.png", color_mask)

    contours, _ = cv2.findContours(color_mask, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    bounding_contour = max(contours, key=cv2.contourArea)
    filtered_contours = [contour for contour in contours if contour is not bounding_contour]

    for contour in filtered_contours:
        x, y, w, h = cv2.boundingRect(contour)

        bars_with_stats.append({
            "x": x,
            "y": y,
            "w": w,
            "h": h,
        })

    return bars_with_stats


def detect_colors_for_grouped_chart(merged_img, legend_bars_data):
    groups_with_bars = {}
    for legend_bar in legend_bars_data:
        bars_with_stats = detect_bars_by_color(merged_img, legend_bar["bgr_color"])
        groups_with_bars[legend_bar["text"]] = {
            "group_color": legend_bar["bgr_color"],
            "bars": bars_with_stats}
    image_detections.print_array("groups_with_bars", groups_with_bars)

    return groups_with_bars


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
    bar_with_color = np.ndarray(resized_color.shape, np.uint8)
    bar_with_color.fill(0)
    bar_with_color[bars_labels == label] = resized_color[bars_labels == label]
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

    dominant_color = unique_colors_with_counts[0][:3].astype(np.uint8)

    threshold = 100

    for i in range(1, len(unique_colors_with_counts)):
        vector_a = unique_colors_with_counts[i][:3].astype(np.uint8)

        dist = np.array(np.linalg.norm(np.array(vector_a, np.int8) - np.array(dominant_color, np.int8)), np.int8)

        ratio = round(
            unique_colors_with_counts[i][3] / (bar_with_color_cropped.shape[0] * bar_with_color_cropped.shape[1]), 3)

        # at least the 50% of the bar has to be in the dominant color
        if dist <= threshold and ratio >= 0.5:
            dominant_color = np.array(np.average([dominant_color, vector_a], axis=0))

    return dominant_color


def merge_legend_bar_colors(bar_stats_with_colors):
    # print(f"\tbar_stats_with_colors: {bar_stats_with_colors}")
    grouped_bgr_colors = []
    similar_color_index = None

    for i, bar_stats in enumerate(bar_stats_with_colors):
        # print(f"{i}. pos: {pos}, color: {color}")
        for j, color_bar in enumerate(grouped_bgr_colors):
            norm = int(
                np.linalg.norm(np.array(color_bar["bgr_color"], np.int8) - np.array(bar_stats["bgr_color"], np.int8)))
            if norm <= similar_color_threshold:
                similar_color_index = j
                break
            else:
                similar_color_index = None
            # print(f"norm: {values['color']} - {color} = {norm}, {key}")
        x = bar_stats["x"]
        y = bar_stats["y"]
        w = bar_stats["w"]
        h = bar_stats["h"]

        if similar_color_index is not None:
            min_x = min(grouped_bgr_colors[similar_color_index]["x"], x)
            min_y = min(grouped_bgr_colors[similar_color_index]["y"], y)
            max_w = max(grouped_bgr_colors[similar_color_index]["x"] + grouped_bgr_colors[similar_color_index]["w"],
                        x + w) - min_x
            max_h = max(grouped_bgr_colors[similar_color_index]["y"] + grouped_bgr_colors[similar_color_index]["h"],
                        y + h) - min_y

            grouped_bgr_colors[similar_color_index]["x"] = min_x
            grouped_bgr_colors[similar_color_index]["y"] = min_y
            grouped_bgr_colors[similar_color_index]["w"] = max_w
            grouped_bgr_colors[similar_color_index]["h"] = max_h

            average = np.array(
                np.average([grouped_bgr_colors[similar_color_index]["bgr_color"], bar_stats["bgr_color"]], axis=0),
                np.uint8)
            # print(f"{grouped_bgr_colors[similar_color_key]['color']} and {color} = {average}")
            grouped_bgr_colors[similar_color_index]["bgr_color"] = average

        else:
            grouped_bgr_colors.append({
                "x": x,
                "y": y,
                "w": w,
                "h": h,
                "bgr_color": bar_stats["bgr_color"]
            })
    # image_detections.print_array("grouped_legend_bgr_colors", grouped_bgr_colors)
    return grouped_bgr_colors


def get_bar_color_for_simple_chart(bar_stats_with_colors):
    # print(f"\tbar_stats_with_colors: {bar_stats_with_colors}")
    grouped_bgr_colors = {}
    threshold = 60
    similar_color_key = None

    for i, bar in enumerate(bar_stats_with_colors):
        # print(f"{i}. pos: {pos}, color: {color}")
        for key, values in grouped_bgr_colors.items():
            norm = int(np.linalg.norm(np.array(values["bgr_color"], np.int8) - np.array(bar["bgr_color"], np.int8)))
            if norm <= threshold:
                similar_color_key = key
                break
            else:
                similar_color_key = None
            # print(f"norm: {values['color']} - {color} = {norm}, {key}")

        if similar_color_key is not None:
            average = np.array(
                np.average([grouped_bgr_colors[similar_color_key]['bgr_color'], bar["bgr_color"]], axis=0),
                np.uint8)
            # print(f"{grouped_bgr_colors[similar_color_key]['color']} and {color} = {average}")
            image_detections.colors = average

        else:
            image_detections.colors = bar["bgr_color"]

    image_detections.print_array("tcolors", image_detections.colors)


def merge_similar_colors(legend_bars_data):
    all_color_bars_img = cv2.bitwise_and(image_edits.img_color, image_edits.img_color,
                                         mask=image_edits.bars_img)
    merged_colors = all_color_bars_img.copy()
    cv2.imwrite("A-merged.png", merged_colors)
    threshold = 20

    for group in legend_bars_data:
        color = group["bgr_color"]
        lower_color = np.clip(np.array(np.array(color, np.int16) - threshold), 0, 255)
        upper_color = np.clip(np.array(np.array(color, np.int16) + threshold), 0, 255)
        mask = cv2.inRange(merged_colors, lower_color, upper_color)
        merged_colors[mask == 255] = color
        cv2.imwrite("A-merged.png", merged_colors)
    return merged_colors


def merge_grouped_chart_bar_colors(bar_stats_with_data):
    bars_with_merged_colors = {}
    threshold = 60
    similar_color_key = None

    for i, bar_stats in enumerate(bar_stats_with_data):
        for key, value in bars_with_merged_colors.items():
            norm = int(
                np.linalg.norm(np.array(value["group_color"], np.int8) - np.array(bar_stats["bgr_color"], np.int8)))
            if norm <= threshold:
                similar_color_key = key
                break
            else:
                similar_color_key = None

        # Similar color
        if similar_color_key is not None:
            bars_with_merged_colors[similar_color_key]["bars"].append(bar_stats)

            average = np.array(
                np.average([bars_with_merged_colors[similar_color_key]["group_color"], bar_stats["bgr_color"]], axis=0),
                np.uint8)
            bars_with_merged_colors[similar_color_key]["group_color"] = average

        # New color
        else:
            bars_with_merged_colors[len(bars_with_merged_colors)] = {
                "group_color": bar_stats["bgr_color"],
                "bars": [bar_stats]
            }
    return bars_with_merged_colors
