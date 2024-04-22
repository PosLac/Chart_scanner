import math
import cv2
import numpy as np

from config import config

logger = config.logger
upscale_rate = 1
THRESHOLD = 230
bars_stats = None
bars_with_labels = None
img_orig_gray = None
img_gray = None
img_color = None
binary = None
hugh = None
bars_img = None


def upscale() -> None:
    """
    Scales up the retrieved image to width reach 1080 for easier scanning

    Returns:
        None
    """
    global img_gray, img_color, upscale_rate
    upscale_rate = round(1080 / img_color.shape[1], 3)

    height = int(img_color.shape[0] * upscale_rate)
    width = int(img_color.shape[1] * upscale_rate)
    img_gray = cv2.resize(img_gray, (width, height))

    height = int(img_color.shape[0] * upscale_rate)
    width = int(img_color.shape[1] * upscale_rate)
    img_color = cv2.resize(img_color, (width, height))
    logger.info(f"Upscale image with {upscale_rate}")


def thresholding(threshold) -> np.ndarray:
    """
    Thresholds image with the given value and returns with the image

    Returns:
        binary (numpy.ndarray):
    """
    global binary, hugh
    binary = np.uint8(np.ndarray(img_gray.shape))
    binary.fill(0)
    binary[img_gray < threshold] = 255
    # cv2.imwrite("A-binary.png", binary)
    return binary


def image_straightening() -> np.ndarray:
    """
    Rotates the image in case that is not straight, updates and returns with the global img_color
    If the rotation of the input image is more than 45°,
    it can rotate the image to a position which is +90° or -90° than the straight image #TODO pontos fok

    Returns:
        None
    """
    global binary, img_orig_gray, img_gray, img_color, hugh

    hugh = cv2.Canny(img_gray, 50, 200, None, 3)
    cdst = cv2.cvtColor(hugh, cv2.COLOR_GRAY2BGR)
    lines = cv2.HoughLines(hugh, 1, np.pi / 180, 140, None, 0, 0)
    sizemax = math.sqrt(cdst.shape[0] ** 2 + cdst.shape[1] ** 2)
    sum_of_degrees = 0

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
                sum_of_degrees = sum_of_degrees + act_deg + 90

            elif act_deg > 135:
                cv2.line(cdst, pt1, pt2, (0, 0, 255), 3, cv2.LINE_AA)
                sum_of_degrees = sum_of_degrees + act_deg - 90

            else:
                cv2.line(cdst, pt1, pt2, (255, 0, 0), 3, cv2.LINE_AA)
                sum_of_degrees = sum_of_degrees + act_deg

    average_rotation = round(sum_of_degrees / len(lines), 3)
    logger.info(f"Rotation of image is {average_rotation}°")
    if average_rotation - 90 > 50 or average_rotation - 90 < -50:
        logger.warn(f"Rotation of image is too big ({average_rotation}), program is unable to straighten it")
    else:
        rows, cols = img_gray.shape[:2]
        m = cv2.getRotationMatrix2D((cols / 2, rows / 2), average_rotation - 90, 1)
        binary = cv2.warpAffine(binary, m, (cols, rows))
        img_gray = cv2.warpAffine(img_gray, m, (cols, rows), borderMode=cv2.BORDER_CONSTANT,
                                  borderValue=(255, 255, 255))
        img_color = cv2.warpAffine(img_color, m, (cols, rows), borderMode=cv2.BORDER_CONSTANT,
                                   borderValue=(255, 255, 255))

        logger.info(f"Rotate image with {average_rotation - 90.0}")
    return img_color


def get_bar_stats(legend_position) -> np.ndarray:
    """
    Delete text and unnecessary objects from image using morphological transformation, and leaves only the bars
    Returns with the remaining object stats (bars) using connected component detection

    Returns:
        bars_stats: stats of the bars
    """
    global bars_img, bars_with_labels, bars_stats, upscale_rate

    img = thresholding(THRESHOLD)
    # cv2.imwrite("A-bars_img1.png", img)
    retval = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))

    bars_img = cv2.erode(img, retval, None, None, 14)
    bars_img = cv2.dilate(bars_img, retval, None, None, 9)
    bars_p = np.ndarray(bars_img.shape)
    bars_p.fill(0)
    bars_p[bars_img > 0] = 255
    bars_img = np.uint8(bars_p)

    # Remove objects in legend
    if legend_position:
        legend_start_x = int(legend_position.topLeft().x() * upscale_rate)
        legend_start_y = int(legend_position.topLeft().y() * upscale_rate)
        legend_end_x = int(legend_position.bottomRight().x() * upscale_rate)
        legend_end_y = int(legend_position.bottomRight().y() * upscale_rate)
        bars_img[legend_start_y:legend_end_y, legend_start_x:legend_end_x] = 0
        # cv2.imwrite("bars_img.png", bars_img)

    _, bars_with_labels, stats, _ = cv2.connectedComponentsWithStats(bars_img, None, 8)
    bars_stats = stats.copy()

    # Remove background
    bars_stats = np.delete(bars_stats, 0, 0)

    if len(bars_stats) == 0:
        raise Exception("Can't detect bars on the image")
    # logger.info(f"Stats of bars: {bars_stats}")
    return bars_stats
