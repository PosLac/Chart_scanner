import cv2
import numpy as np
import pytesseract
from pytesseract import Output
import functions.image_detections as detects
from functions import image_edits as edits, color_detections, image_detections

top_right_point = None
bottom_left_point = None


def detect_legend_bars(legend):
    bars_stats, bars_with_labels = morph_transform_for_legend(legend)
    bars_with_colors = color_detections.detect_colors(legend, bars_stats, bars_with_labels)

    return bars_with_colors


def morph_transform_for_legend(img):
    legend_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    legend_binary = np.ndarray(legend_gray.shape, np.uint8)
    legend_binary.fill(0)
    legend_binary[legend_gray < 220] = 255

    retval = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    bars = cv2.dilate(legend_binary, retval, None, None, 1)
    bars = cv2.erode(bars, retval, None, None, 4)
    bars = cv2.dilate(bars, retval, None, None, 3)

    # cv2.imshow("bars", bars)

    bars_p = np.ndarray(bars.shape)
    bars_p.fill(0)
    bars_p[bars > 0] = 255
    bars = np.uint8(bars_p)

    _, labels, stats, _ = cv2.connectedComponentsWithStats(bars, None, 8)

    # Delete background
    stats = np.delete(stats, 0, 0)

    return stats, labels


def detect_legend_texts(bars_max_x):
    legend_orig = detects.legend_without_bars

    cv2.imwrite("legend_orig.png", legend_orig)
    legend_gray = cv2.cvtColor(legend_orig, cv2.COLOR_BGR2GRAY)

    legend_binary = np.ndarray(legend_gray.shape, np.uint8())
    legend_binary.fill(255)
    legend_binary[legend_gray < 220] = 0

    cv2.imwrite("legend_binary_inv.png", legend_binary)

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

    image_detections.print_array("merged_texts", merged_texts)

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
                    "color": bar["color"],
                    "bar_x": bar["x"],
                    "bar_y": bar["y"],
                    "bar_w": bar["w"],
                    "bar_h": bar["h"],
                    "text": t_values["text"]
                })
    image_detections.print_array("bars_with_texts", bars_with_texts)
    return bars_with_texts


def detect_legend_position():
    global top_right_point, bottom_left_point
    _, thresholded = cv2.threshold(edits.img_gray, 220, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(thresholded, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

    bounding_rect_contour = None

    min_area = (edits.img_gray.shape[0] * edits.img_gray.shape[1]) * 0.5

    # First element is the bounding contour, so skipped
    for i in range(1, len(contours)):
        if cv2.contourArea(contours[i]) >= min_area:
            bounding_rect_contour = contours[i]
            break

    top_right_point = bounding_rect_contour[0][0]
    bottom_left_point = bounding_rect_contour[0][0]

    for point in bounding_rect_contour:
        point = point[0]

        if point[0] >= top_right_point[0] and point[1] <= top_right_point[1]:
            top_right_point = point

        if point[0] <= bottom_left_point[0] and point[1] >= bottom_left_point[1]:
            bottom_left_point = point

    top_right_point = (top_right_point[0] // edits.UPSCALE_RATE, top_right_point[1] // edits.UPSCALE_RATE)
    print(f"top_right_point: {top_right_point}")

    bottom_left_point = (bottom_left_point[0] // edits.UPSCALE_RATE, bottom_left_point[1] // edits.UPSCALE_RATE)
    print(f"bottom_left_point: {bottom_left_point}")


def add_text_to_bars(bars, legend_bars):
    threshold = 60
    text_groups = {}

    for bar_with_text in legend_bars:
        for key, values in bars.items():
            norm = int(np.linalg.norm(np.array(values["group_color"], np.int8) - np.array(bar_with_text["color"], np.int8)))
            if norm <= threshold:
                text_groups[bar_with_text["text"]] = {
                    "group_color": values["group_color"],
                    "bars": values["bars"]
                }
    return text_groups
