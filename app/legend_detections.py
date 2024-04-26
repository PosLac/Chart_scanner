import cv2
import numpy as np
import pytesseract
from pytesseract import Output
from app import image_edits, color_detections, image_detections
from config import config

logger = config.logger
chart_border_polygon_resized = None


def detect_legend_bars(legend: np.ndarray) -> list:
    """
    Detects bars in cropped legend

    Args:
        legend: image of cropped legend

    Returns:
        bars_with_colors: detected bars with colors
    """
    bars_stats, bars_with_labels = morph_transform_for_legend(legend)
    bars_with_colors = color_detections.detect_colors(legend, bars_stats, bars_with_labels)

    return bars_with_colors


def morph_transform_for_legend(img: np.ndarray) -> [list, list]:
    """
    Removes text and small objects from cropped legend with morphological transformation

    Args:
        img: image of cropped legend

    Returns:
        stats:  stats of detected objects (bars)
        labels: labels for detected objects (bars)
    """
    legend_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    legend_binary = np.ndarray(legend_gray.shape, np.uint8)
    legend_binary.fill(0)
    legend_binary[legend_gray < 240] = 255
    retval = cv2.getStructuringElement(cv2.MORPH_RECT, (7, 7))
    temp_bars = legend_binary.copy()
    iterations = 0

    for iterations in range(1, 10):
        temp_bars = cv2.erode(temp_bars, retval, None, None, 1)
        _, _, stats, _ = cv2.connectedComponentsWithStats(temp_bars, None, 8)
        if len(stats) == 1:
            break

    bars = cv2.erode(legend_binary, retval, None, None, iterations - 1)

    bars = cv2.dilate(bars, retval, None, None, iterations - 1)
    _, labels, stats, _ = cv2.connectedComponentsWithStats(bars, None, 8)

    # Delete background
    stats = np.delete(stats, 0, 0)

    return stats, labels


def detect_legend_texts(bars_max_x: int) -> dict:
    """
    Detects text from cropped legend

    Args:
        bars_max_x: x coordinate of the rightest bar, text can be only right from this

    Returns:
        merged_texts: merged texts for bars
    """
    legend_orig = image_detections.legend_without_bars

    legend_gray = cv2.cvtColor(legend_orig, cv2.COLOR_BGR2GRAY)

    legend_binary = np.ndarray(legend_gray.shape, np.uint8())
    legend_binary.fill(255)
    legend_binary[legend_gray < 230] = 0

    config_title = r'--oem 3 --psm 1'
    legend_data = pytesseract.pytesseract.image_to_data(legend_binary, config=config_title, output_type=Output.DICT,
                                                        lang='hun')
    n = len(legend_data['level'])

    text_lines = []
    for i in range(n):
        text = legend_data['text'][i]
        conf = legend_data['conf'][i]
        x = legend_data['left'][i]
        y = legend_data['top'][i]
        w = legend_data['width'][i]
        h = legend_data['height'][i]

        if conf >= 60 and text.strip() != "" and bars_max_x <= x:
            text_lines.append((text, y + h, x, y, w, h))

    grouped_texts = {}
    threshold = 10
    for i, (text, bottom, x, y, w, h) in enumerate(text_lines):
        has_key_in_range = next((key for key in grouped_texts.keys() if abs(key - bottom) <= threshold), None)
        if has_key_in_range:
            if grouped_texts[has_key_in_range]["x"] < x:
                grouped_texts[has_key_in_range]["text"].append(text)
                grouped_texts[has_key_in_range]["w"] = x + w - grouped_texts[has_key_in_range]["x"]

            else:
                temp_text = grouped_texts[has_key_in_range]["text"]
                grouped_texts[has_key_in_range]["text"] = [text]
                grouped_texts[has_key_in_range]["text"].extend(temp_text)
                grouped_texts[has_key_in_range]["w"] = grouped_texts[has_key_in_range]["x"] + grouped_texts[has_key_in_range]["w"] - x
                grouped_texts[has_key_in_range]["x"] = x

        else:
            grouped_texts[bottom] = {
                "text": [text],
                "x": x,
                "y": y,
                "w": w,
                "h": h
            }

    merged_texts = {}
    for i, (key, values) in enumerate(grouped_texts.items()):
        merged_texts[i] = values
        merged_texts[i]["text"] = " ".join(values["text"])

    return merged_texts


def merge_bars_with_texts(bars: list, texts: dict) -> list:
    """
    Add text to bars

    Args:
        bars:    stats of bars
        texts:  detected texts

    Returns:
        bars_with_texts: bar stats with texts
    """
    threshold = 10
    bars_with_texts = []

    for bar in bars:
        bar_bottom = bar["y"] + bar["h"]

        for t_key, t_values in texts.items():
            text_bottom = t_values["y"] + t_values["h"]
            if abs(text_bottom - bar_bottom) <= threshold:
                bars_with_texts.append({
                    "bgr_color": bar["bgr_color"],
                    "bar_x": bar["x"],
                    "bar_y": bar["y"],
                    "bar_w": bar["w"],
                    "bar_h": bar["h"],
                    "text": t_values["text"]
                })
    return bars_with_texts


def detect_legend_position() -> None:
    """
    Define the top right point of the chart border to position the legend

    Returns:
        None

    Raises:
        Exception: raised when can't define the chart border
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

