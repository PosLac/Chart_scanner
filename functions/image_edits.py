import math

import cv2
import numpy as np

UPSCALE_RATE = 2
NUM_SIZE = 0
K = -1
BLOCK_SIZE = 5

resized_gray = None
resized_color = None
elements = None
bars_with_labels = None
img_orig_gray = None
img_orig_color = None
img_gray = None
img_color = None
binary = None
hugh = None


def read_img(file_name: str) -> np.ndarray:
    """
    Reads image and convert to grayscale

    Args:
        file_name (str): path to the image

    Returns:
        img (numpy.ndarray): retrieved gray image
    """
    global img_gray, img_color, img_orig_gray, img_orig_color

    img_orig_color = cv2.imread(file_name, cv2.IMREAD_COLOR)
    img_orig_gray = cv2.cvtColor(img_orig_color, cv2.COLOR_BGR2GRAY)
    img_gray = img_orig_gray.copy()
    img_color = img_orig_color.copy()
    return img_gray


def upscale() -> None:
    """
    Scales up the retrieved image with the given upscale value for easier scanning

    Returns:
        None
    """
    global img_gray, img_color, NUM_SIZE, resized_gray, resized_color

    height = int(img_gray.shape[0] * UPSCALE_RATE)
    width = int(img_gray.shape[1] * UPSCALE_RATE)

    img_gray = cv2.resize(img_gray, (width, height))
    NUM_SIZE = img_gray.shape[0] * img_gray.shape[1] / 1000  # todo what is NUM_SIZE?
    resized_gray = img_gray.copy()

    height = int(img_color.shape[0] * UPSCALE_RATE)
    width = int(img_color.shape[1] * UPSCALE_RATE)
    img_color = cv2.resize(img_color, (width, height))
    resized_color = img_color.copy()


def ni_black_threshold() -> None:
    """
    Thresholding of the image

    Returns:
        None
    """
    global img_gray
    img_gray = cv2.ximgproc.niBlackThreshold(img_gray, 255, cv2.THRESH_TRUNC, BLOCK_SIZE, K, binarizationMethod=0,
                                             r=108)


def threshold() -> np.ndarray:
    """
    Converts binary

    Returns:
        binary (numpy.ndarray):
    """
    global binary, hugh
    binary = np.uint8(np.ndarray(img_gray.shape))
    binary.fill(0)
    binary[img_gray < 220] = 255
    # imshow_resized("img_gray", img_gray, 0.5)
    # imshow_resized("binary", binary, 0.5)
    hugh = cv2.Canny(img_gray, 50, 200, None, 3)
    return binary


def rotate():
    """
    Rotates the picture if not straight

    """
    global binary, UPSCALE_RATE, img_orig_gray, resized_gray, img_gray

    cdst = cv2.cvtColor(hugh, cv2.COLOR_GRAY2BGR)

    lines = None
    expectation = 200 * UPSCALE_RATE
    while lines is None or len(lines) < 10:
        lines = cv2.HoughLines(hugh, 1, np.pi / 50, expectation, None, 0, 0)
        expectation = expectation - 5

    sizemax = math.sqrt(cdst.shape[0] ** 2 + cdst.shape[1] ** 2)
    all_deg = 0

    if lines is not None:
        for i in range(0, len(lines)):
            rho = lines[i][0][0]
            theta = lines[i][0][1]
            a = math.cos(theta)
            b = math.sin(theta)
            x0 = a * rho
            y0 = b * rho
            act_deg = theta * 180 / math.pi

            pt1 = (int(x0 + sizemax * (-b)), int(y0 + sizemax * a))
            pt2 = (int(x0 - sizemax * (-b)), int(y0 - sizemax * a))

            if 0 <= act_deg < 45:
                cv2.line(cdst, pt1, pt2, (0, 0, 255), 3, cv2.LINE_AA)
                all_deg = all_deg + act_deg + 90

            elif act_deg > 135:
                cv2.line(cdst, pt1, pt2, (0, 0, 255), 3, cv2.LINE_AA)
                all_deg = all_deg + act_deg - 90

            else:
                cv2.line(cdst, pt1, pt2, (255, 0, 0), 3, cv2.LINE_AA)
                all_deg = all_deg + act_deg

    avr = all_deg / len(lines)

    rows, cols = img_gray.shape[:2]
    m = cv2.getRotationMatrix2D((cols / 2, rows / 2), avr - 90, 1)
    rot = cv2.warpAffine(hugh, m, (cols, rows))
    binary = cv2.warpAffine(binary, m, (cols, rows))
    resized_gray = cv2.warpAffine(resized_gray, m, (cols, rows))
    img_gray = cv2.warpAffine(img_gray, m, (cols, rows))


def morphological_transform(img) -> np.ndarray:
    """

    """
    global bar_hs, chart_with_bars_img, bars, bars_with_labels
    # cv2.imshow('chart_with_bars_img', chart_with_bars_img)
    retval = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    bars = cv2.dilate(img, retval)
    bars = cv2.erode(bars, retval, None, None, 7)
    bars = cv2.erode(bars, retval, None, None, 7)
    bars = cv2.dilate(bars, retval, None, None, 4)
    bars = cv2.dilate(bars, retval, None, None, 4)
    # imshow_resized("bars1", bars, 0.5)
    bars_p = np.ndarray(bars.shape)
    bars_p.fill(0)
    bars_p[bars > 0] = 255
    bars = np.uint8(bars_p)
    # imshow_resized("bars2", bars, 0.5)
    # cv2.imwrite('bars1.png', bars)

    _, bars_with_labels, stats, _ = cv2.connectedComponentsWithStats(bars, None, 8)
    print('\tstat_len: ', len(stats))
    # print('stats2: ', stats)
    elements = stats.copy()

    # Háttér kitörlése
    elements = np.delete(elements, 0, 0)
    return elements


# todo összevonni legend és többi morph trans-t


# TODO delete,  just for funs:
def imshow_resized(name, img, ratio=0.5):
    resized_img = cv2.resize(img, (int(img.shape[1] * ratio), int(img.shape[0] * ratio)))
    cv2.imshow(f"{name}", resized_img)


def show_color(name, color):
    color_img = np.ndarray((200, 200, 3), np.uint8)
    color_img[:] = color
    cv2.imshow(name, color_img)
