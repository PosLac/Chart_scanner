import math

import cv2
import numpy as np

upscale_rate = 1
NUM_SIZE = 0
K = -1
BLOCK_SIZE = 5

resized_color = None
bars_stats = None
bars_with_labels = None
img_orig_gray = None
img_orig_color = None
img_gray = None
img_color = None
binary = None
hugh = None
bars_img = None


def read_img(file_name: str) -> np.ndarray:
    """
    Reads image and convert to grayscale

    Args:
        file_name (str): path to the image

    Returns:
        img (numpy.ndarray): retrieved gray image
    """
    global img_gray, img_color, img_orig_gray, img_orig_color

    with open(file_name, 'rb') as file:
        buffer = np.asarray(bytearray(file.read()), dtype=np.uint8)
        img_orig_color = cv2.imdecode(buffer, cv2.IMREAD_COLOR)

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
    global img_gray, img_color, upscale_rate
    upscale_rate = 1080 / img_color.shape[1]

    height = int(img_color.shape[0] * upscale_rate)
    width = int(img_color.shape[1] * upscale_rate)
    img_gray = cv2.resize(img_gray, (width, height))

    height = int(img_color.shape[0] * upscale_rate)
    width = int(img_color.shape[1] * upscale_rate)
    img_color = cv2.resize(img_color, (width, height))
    print(f"\tUpscale image with {upscale_rate}")


def ni_black_threshold() -> None:
    """
    Thresholding of the image

    Returns:
        None
    """
    global img_gray
    img_gray = cv2.ximgproc.niBlackThreshold(img_gray, 200, cv2.THRESH_TRUNC, BLOCK_SIZE, K, binarizationMethod=0,
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
    binary[img_gray < 230] = 255
    cv2.imwrite("A-binary.png", binary)
    # hugh = cv2.Canny(img_gray, 50, 200, None, 3)
    return binary


def image_straightening():
    """
    Rotates the picture if not straight

    """
    global binary, img_orig_gray, img_gray, img_color, hugh

    hugh = cv2.Canny(img_gray, 50, 200, None, 3)
    cdst = cv2.cvtColor(hugh, cv2.COLOR_GRAY2BGR)
    lines = cv2.HoughLines(hugh, 1, np.pi / 180, 140, None, 0, 0)

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

    average_rotation = all_deg / len(lines)
    print(f"\tRotate image with {average_rotation}°")
    if average_rotation - 90 > 50 or average_rotation - 90 < -50:
        print(f"\tRotation of image is too big, program is unable to straighten it")  # TODO hogyan tovább
    else:
        rows, cols = img_gray.shape[:2]
        m = cv2.getRotationMatrix2D((cols / 2, rows / 2), average_rotation - 90, 1)
        binary = cv2.warpAffine(binary, m, (cols, rows))
        img_gray = cv2.warpAffine(img_gray, m, (cols, rows), borderMode=cv2.BORDER_CONSTANT,
                                  borderValue=(255, 255, 255))
        img_color = cv2.warpAffine(img_color, m, (cols, rows), borderMode=cv2.BORDER_CONSTANT,
                                   borderValue=(255, 255, 255))
        print("Image straightening done")
    return img_color


def morphological_transform(legend_position) -> np.ndarray:
    """

    """
    global bars_img, bars_with_labels, bars_stats, upscale_rate

    img = threshold()
    cv2.imwrite("A-bars_img1.png", img)
    retval = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))

    bars_img = cv2.erode(img, retval, None, None, 14)
    bars_img = cv2.dilate(bars_img, retval, None, None, 9)
    bars_p = np.ndarray(bars_img.shape)
    bars_p.fill(0)
    bars_p[bars_img > 0] = 255
    bars_img = np.uint8(bars_p)

    # Remove legend bars
    if legend_position:
        legend_start_x = int(legend_position.topLeft().x() * upscale_rate)
        legend_start_y = int(legend_position.topLeft().y() * upscale_rate)
        legend_end_x = int(legend_position.bottomRight().x() * upscale_rate)
        legend_end_y = int(legend_position.bottomRight().y() * upscale_rate)
        bars_img[legend_start_y:legend_end_y, legend_start_x:legend_end_x] = 0
        cv2.imwrite("bars_img.png", bars_img)

    _, bars_with_labels, stats, _ = cv2.connectedComponentsWithStats(bars_img, None, 8)
    bars_stats = stats.copy()

    # Remove background
    bars_stats = np.delete(bars_stats, 0, 0)
    return bars_stats
