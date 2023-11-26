import math
import cv2
import numpy
import main.image_detectations as detects

UPSCALE_RATE = 2
NUM_SIZE = 0
K = -1
BLOCK_SIZE = 5

resized = None
elements = None
img_original = None
img = None
binary = None
hugh = None


def read_img(file_name: str) -> numpy.ndarray:
    """
    Reads image and convert to grayscale

    Args:
        file_name (str): path to the image

    Returns:
        img (numpy.ndarray): retrieved gray image
    """
    global img, img_original

    img_original = cv2.imread(file_name, cv2.IMREAD_GRAYSCALE)
    img = img_original.copy()
    return img


def upscale() -> None:
    """
    Scales up the retrieved image with the given upscale value for easier scanning

    Returns:
        None
    """
    global img, NUM_SIZE, resized

    height = int(img.shape[0] * UPSCALE_RATE)
    width = int(img.shape[1] * UPSCALE_RATE)
    img = cv2.resize(img, (width, height))
    NUM_SIZE = img.shape[0] * img.shape[1] / 1000  # todo what is NUM_SIZE?
    resized = img.copy()


def ni_black_threshold() -> None:
    """
    Thresholding of the image

    Returns:
        None
    """
    global img
    img = cv2.ximgproc.niBlackThreshold(img, 255, cv2.THRESH_TRUNC, BLOCK_SIZE, K, binarizationMethod=0, r=108)


def threshold() -> numpy.ndarray:
    """
    Converts binary

    Returns:
        binary (numpy.ndarray):
    """
    global binary, hugh
    binary = numpy.uint8(numpy.ndarray(img.shape))
    binary.fill(0)
    binary[img < 200] = 255
    hugh = cv2.Canny(img, 50, 200, None, 3)
    # cv2.imshow("hugh", hugh)
    return binary


def rotate():
    """
    Rotates the picture if not straight

    """
    global binary, UPSCALE_RATE, img_original, resized, img

    cdst = cv2.cvtColor(hugh, cv2.COLOR_GRAY2BGR)

    lines = None
    expectation = 200 * UPSCALE_RATE
    while lines is None or len(lines) < 10:
        lines = cv2.HoughLines(hugh, 1, numpy.pi / 50, expectation, None, 0, 0)
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

    rows, cols = img.shape[:2]
    m = cv2.getRotationMatrix2D((cols / 2, rows / 2), avr - 90, 1)
    rot = cv2.warpAffine(hugh, m, (cols, rows))
    binary = cv2.warpAffine(binary, m, (cols, rows))
    resized = cv2.warpAffine(resized, m, (cols, rows))
    img = cv2.warpAffine(img, m, (cols, rows))


def morphological_transform() -> None:
    """

    """
    global elements, bar_hs, chart_with_bars_img, bars
    # cv2.imshow('chart_with_bars_img', chart_with_bars_img)
    retval = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    bars = cv2.dilate(detects.chart_with_bars_img, retval)
    bars = cv2.erode(bars, retval, None, None, 7)
    bars = cv2.erode(bars, retval, None, None, 7)
    bars = cv2.dilate(bars, retval, None, None, 4)
    bars = cv2.dilate(bars, retval, None, None, 4)
    # cv2.imshow('bars', bars)
    bars_p = numpy.ndarray(bars.shape)
    bars_p.fill(0)
    bars_p[bars > 0] = 255
    bars = numpy.uint8(bars_p)
    # cv2.imwrite('bars1.png', bars)

    _, _, stats, _ = cv2.connectedComponentsWithStats(bars, None, 8)
    # cv2.imshow('bars', bars)
    # print('stat_len: ', len(stats))
    # print('stats2: ', stats)
    elements = stats.copy()

    # Háttér kitörlése
    elements = numpy.delete(elements, 0, 0)
