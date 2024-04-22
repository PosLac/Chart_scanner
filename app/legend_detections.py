import cv2
import numpy as np
import pytesseract
from pytesseract import Output
from app import image_edits, color_detections, image_detections
from config import config

logger = config.logger
chart_border_polygon_resized = None


def detect_legend_bars(legend):
    bars_stats, bars_with_labels = morph_transform_for_legend(legend)
    bars_with_colors = color_detections.detect_colors(legend, bars_stats, bars_with_labels)

    return bars_with_colors


def morph_transform_for_legend(img):
    legend_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    legend_binary = np.ndarray(legend_gray.shape, np.uint8)
    legend_binary.fill(0)
    legend_binary[legend_gray < 240] = 255
    # cv2.imwrite("A-legend_threshold.png", legend_binary)
    retval = cv2.getStructuringElement(cv2.MORPH_RECT, (7, 7))
    temp_bars = legend_binary.copy()
    iterations = 0

    for iterations in range(1, 10):
        temp_bars = cv2.erode(temp_bars, retval, None, None, 1)
        _, _, stats, _ = cv2.connectedComponentsWithStats(temp_bars, None, 8)
        # cv2.imwrite(f"A-legend_bars {iterations}.png", temp_bars)
        if len(stats) == 1:
            break

    bars = cv2.erode(legend_binary, retval, None, None, iterations - 1)
    # cv2.imwrite(f"A-legend_bars erode {iterations - 1}.png", bars)

    bars = cv2.dilate(bars, retval, None, None, iterations - 1)
    # cv2.imwrite(f"A-legend_bars dilate {iterations - 1}.png", bars)
    _, labels, stats, _ = cv2.connectedComponentsWithStats(bars, None, 8)

    # Delete background
    stats = np.delete(stats, 0, 0)

    return stats, labels


def detect_legend_texts(bars_max_x):
    legend_orig = image_detections.legend_without_bars

    # cv2.imwrite("legend_orig.png", legend_orig)
    legend_gray = cv2.cvtColor(legend_orig, cv2.COLOR_BGR2GRAY)

    legend_binary = np.ndarray(legend_gray.shape, np.uint8())
    legend_binary.fill(255)
    legend_binary[legend_gray < 230] = 0

    # cv2.imwrite("legend_binary_inv.png", legend_binary)

    config_title = r'--oem 3 --psm 1'
    # print(f"legend_text: {legend_text}")
    legend_data = pytesseract.pytesseract.image_to_data(legend_binary, config=config_title, output_type=Output.DICT,
                                                        lang='hun')
    n = len(legend_data['level'])

    text_lines = []
    for i in range(n):
        # print(legend_data[i])
        text = legend_data['text'][i]
        conf = legend_data['conf'][i]
        x = legend_data['left'][i]
        y = legend_data['top'][i]
        w = legend_data['width'][i]
        h = legend_data['height'][i]

        if conf >= 60 and text.strip() != "" and bars_max_x <= x:
            # print(f"conf: {conf}, text: {text}")
            text_lines.append((text, y + h, x, y, w, h))

    # print(f"text_lines all: {text_lines}")

    grouped_texts = {}
    threshold = 10
    for i, (text, bottom, x, y, w, h) in enumerate(text_lines):
        has_key_in_range = next((key for key in grouped_texts.keys() if abs(key - bottom) <= threshold), None)
        if has_key_in_range:
            if grouped_texts[has_key_in_range]["x"] < x:
                grouped_texts[has_key_in_range]["text"].append(text)
                grouped_texts[has_key_in_range]["w"] = x + w - grouped_texts[has_key_in_range]["x"]

            # elem előbb kezdődik, mint ami már van
            else:
                temp_text = grouped_texts[has_key_in_range]["text"]
                grouped_texts[has_key_in_range]["text"] = [text]
                grouped_texts[has_key_in_range]["text"].extend(temp_text)
                grouped_texts[has_key_in_range]["w"] = grouped_texts[has_key_in_range]["x"] + \
                                                       grouped_texts[has_key_in_range]["w"] - x
                grouped_texts[has_key_in_range]["x"] = x

        else:
            grouped_texts[bottom] = {
                "text": [text],
                "x": x,
                "y": y,
                "w": w,
                "h": h
            }

    # print(f"text_lines before merge: {grouped_texts}")
    merged_texts = {}
    for i, (key, values) in enumerate(grouped_texts.items()):
        merged_texts[i] = values
        merged_texts[i]["text"] = " ".join(values["text"])

    # image_detections.print_array("merged_texts", merged_texts)

    for key, values in merged_texts.items():
        text = values["text"]
        x = values["x"]
        y = values["y"]
        w = values["w"]
        h = values["h"]

        cv2.rectangle(legend_orig, (x, y), (x + w, y + h), (0, 255, 0), 2)
        cv2.putText(legend_orig, text, (x, y + h + 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
        # cv2.imshow("legend_orig", legend_orig)

    return merged_texts


def merge_bars_with_texts(bars, texts):
    threshold = 10
    bars_with_texts = []

    for bar in bars:
        bar_bottom = bar["y"] + bar["h"]
        # print(f"bar_bottom: {bar_bottom}")

        for t_key, t_values in texts.items():
            text_bottom = t_values["y"] + t_values["h"]
            if abs(text_bottom - bar_bottom) <= threshold:
                # print(f"text_bottom: {text_bottom}")
                bars_with_texts.append({
                    "bgr_color": bar["bgr_color"],
                    "bar_x": bar["x"],
                    "bar_y": bar["y"],
                    "bar_w": bar["w"],
                    "bar_h": bar["h"],
                    "text": t_values["text"]
                })
    # image_detections.print_array("bars_with_texts", bars_with_texts)
    return bars_with_texts


def detect_legend_position() -> None:
    """
    Define the top right point of the chart border to position the legend

    Returns:
        None
    """
    global chart_border_polygon_resized

    chart_border_polygon_resized = []
    _, thresholded = cv2.threshold(image_edits.img_gray, 220, 255, cv2.THRESH_BINARY)
    contours, hierarchy = cv2.findContours(thresholded, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    min_area = (image_edits.img_gray.shape[0] * image_edits.img_gray.shape[1]) * 0.3

    filtered_contours = []
    for i in range(len(contours)):
        if min_area <= cv2.contourArea(contours[i]) and hierarchy[0][i][0] != -1:
            filtered_contours.append(contours[i])

    chart_border_contour = sorted(filtered_contours, key=lambda x: cv2.contourArea(x), reverse=True)[0]
    epsilon = 30
    i = 0
    chart_border_poligon = []

    while len(chart_border_poligon) != 4 and i < 100:
        chart_border_poligon = cv2.approxPolyDP(chart_border_contour, epsilon, True)
        epsilon += 30
        i += 1

    if len(chart_border_poligon) != 4:
        logger.error("Can't detect chart border, use default legend position")
        raise Exception("Can't detect chart border, use default legend position")

    for point in chart_border_poligon:
        chart_border_polygon_resized.append(
            [int(point[0][0] // image_edits.upscale_rate),
             int(point[0][1] // image_edits.upscale_rate)])


def add_text_to_bars(bars, legend_bars):
    threshold = 40
    text_groups = {}

    for bar_with_text in legend_bars:
        for key, values in bars.items():
            norm = int(np.linalg.norm(
                np.array(values["group_color"], np.int8) - np.array(bar_with_text["bgr_color"], np.int8)))
            if norm <= threshold:
                text_groups[bar_with_text["text"]] = {
                    "group_color": values["group_color"],
                    "bars": values["bars"]
                }
    return text_groups
