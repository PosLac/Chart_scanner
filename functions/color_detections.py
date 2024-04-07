import numpy as np

from functions import image_detections


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
        bars_with_colors.append({
            "x": bar_stats[i][0],
            "y": bar_stats[i][1],
            "w": bar_stats[i][2],
            "h": bar_stats[i][3],
            "color": np.array(color_rgb)
        })
        # print(f"{i}. (stats: {bar_stats[i]}) \t (color: {color_rgb})")
        bars_img[bars_labels == i + 1] = 255
    # image_detections.print_array("bars_with_colors", bars_with_colors)
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

        dist = np.array(np.linalg.norm(np.array(vector_a, np.int8) - np.array(dominant_color, np.int8)), np.int8)

        ratio = round(
            unique_colors_with_counts[i][3] / (bar_with_color_cropped.shape[0] * bar_with_color_cropped.shape[1]), 3)

        # at least the 50% of the bar has to be in the dominant color
        if dist <= threshold and ratio >= 0.5:
            dominant_color = np.array(np.average([dominant_color, vector_a], axis=0))[::-1]  # BGR -> RGB

    return dominant_color


def merge_legend_bar_colors(bar_stats_with_colors):
    # print(f"\tbar_stats_with_colors: {bar_stats_with_colors}")
    grouped_bgr_colors = []
    threshold = 40
    similar_color_index = None

    for i, bar_stats in enumerate(bar_stats_with_colors):
        # print(f"{i}. pos: {pos}, color: {color}")
        for j, color_bar in enumerate(grouped_bgr_colors):
            norm = int(np.linalg.norm(np.array(color_bar["color"], np.int8) - np.array(bar_stats["color"], np.int8)))
            if norm <= threshold:
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
                np.average([grouped_bgr_colors[similar_color_index]['color'], bar_stats["color"]], axis=0),
                np.uint8)
            # print(f"{grouped_bgr_colors[similar_color_key]['color']} and {color} = {average}")
            grouped_bgr_colors[similar_color_index]["color"] = average

        else:
            grouped_bgr_colors.append({
                "x": x,
                "y": y,
                "w": w,
                "h": h,
                "color": bar_stats["color"]
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
            norm = int(np.linalg.norm(np.array(values['color'], np.int8) - np.array(bar["color"], np.int8)))
            if norm <= threshold:
                similar_color_key = key
                break
            else:
                similar_color_key = None
            # print(f"norm: {values['color']} - {color} = {norm}, {key}")

        if similar_color_key is not None:
            average = np.array(np.average([grouped_bgr_colors[similar_color_key]['color'], bar["color"]], axis=0),
                               np.uint8)
            # print(f"{grouped_bgr_colors[similar_color_key]['color']} and {color} = {average}")
            image_detections.colors = average

        else:
            image_detections.colors = bar["color"]

    print(f"\tcolors: {image_detections.colors}")


def merge_grouped_chart_bar_colors(bar_stats_with_data):
    bars_with_merged_colors = {}
    threshold = 60
    similar_color_key = None

    for i, bar_stats in enumerate(bar_stats_with_data):
        # print(f"{i}. pos: {pos}, color: {color}")
        for key, value in bars_with_merged_colors.items():
            norm = int(np.linalg.norm(np.array(value["group_color"], np.int8) - np.array(bar_stats["color"], np.int8)))
            if norm <= threshold:
                similar_color_key = key
                break
            else:
                similar_color_key = None
            # print(f"norm: {values['color']} - {color} = {norm}, {key}")

        # Similar color
        if similar_color_key is not None:
            bars_with_merged_colors[similar_color_key]["bars"].append(bar_stats)

            average = np.array(
                np.average([bars_with_merged_colors[similar_color_key]["group_color"], bar_stats["color"]], axis=0),
                np.uint8)
            # print(f"{grouped_bgr_colors[similar_color_key]['color']} and {color} = {average}")
            bars_with_merged_colors[similar_color_key]["group_color"] = average

        # New color
        else:
            bars_with_merged_colors[len(bars_with_merged_colors)] = {
                "group_color": bar_stats["color"],
                "bars": [bar_stats]
            }
    return bars_with_merged_colors
