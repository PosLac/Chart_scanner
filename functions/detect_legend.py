import cv2
import numpy as np
import pytesseract
from pytesseract import Output
import functions.image_detectations as detects
from functions.image_edits import img_gray


def detect_legend_bars(legend):
    bars_stats, bars_with_labels = morph_transform_for_legend(legend)
    bars_with_colors = detects.detect_colors(legend, bars_stats, bars_with_labels)

    return bars_with_colors


def morph_transform_for_legend(img):
    legend_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    legend_binary = np.uint8(np.ndarray(legend_gray.shape))
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
    legend_orig = detects.legend_orig

    # cv2.imshow("legend_orig", legend_orig)
    legend_gray = cv2.cvtColor(legend_orig, cv2.COLOR_BGR2GRAY)

    legend_binary = np.ndarray(legend_gray.shape, np.uint8())
    legend_binary.fill(255)
    legend_binary[legend_gray < 220] = 0

    cv2.imwrite("legend_binary_inv.png", legend_binary)

    config_title = r'--oem 3 --psm 1'
    # print(f"legend_text: {legend_text}")
    legend_data = pytesseract.pytesseract.image_to_data(legend_binary, config=config_title, output_type=Output.DICT)
    # print(f"legend_data: {legend_data['text']}")
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

        if conf > 70 and text.strip() != "" and bars_max_x <= x:
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

    print("\tmerged_texts: {\n\t\t" + "\n\t\t".join(f"{key}: {values}" for key, values in merged_texts.items()) + "}")
    for key, values in merged_texts.items():
        text = values["text"]
        x = values["x"]
        y = values["y"]
        w = values["w"]
        h = values["h"]

        cv2.rectangle(legend_orig, (x, y), (x + w, y + h), (0, 255, 0), 2)
        cv2.putText(legend_orig, text, (x, y + h + 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
        cv2.imshow("legend_orig", legend_orig)

    return merged_texts


def merge_bars_with_texts(bars, texts):
    threshold = 10
    bars_with_texts = {}

    for key, values in bars.items():
        bar_bottom = values["y"] + values["h"]
        # print(f"bar_bottom: {bar_bottom}")

        for t_key, t_values in texts.items():
            text_bottom = t_values["y"] + t_values["h"]
            if abs(text_bottom - bar_bottom) <= threshold:
                # print(f"text_bottom: {text_bottom}")
                bars_with_texts[key] = {
                    "bar_color": values["color"],
                    "bar_x": values["x"],
                    "bar_y": values["y"],
                    "bar_w": values["w"],
                    "bar_h": values["h"],
                    "text": t_values["text"]
                }

    print("\tbars_with_texts: {\n\t\t" + "\n\t\t".join(
        f"{key}: {values}" for key, values in bars_with_texts.items()) + "}")

    return bars_with_texts
