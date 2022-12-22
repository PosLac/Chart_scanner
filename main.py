import cv2
import numpy as np

# chart_origin = cv2.imread('chart_01.png', cv2.IMREAD_GRAYSCALE)
# chart_origin = cv2.imread('chart_ybar.png', cv2.IMREAD_GRAYSCALE)
chart_origin = cv2.imread('chart_xbar.png', cv2.IMREAD_GRAYSCALE)
chart = chart_origin.copy()
# percent = 70
# width = int(chart.shape[1] * percent/100)
# height = int(chart.shape[0] * percent/100)
# chart = cv2.resize(chart, (width, height))
cv2.imwrite('chart_resized.png', chart)
cv2.imshow('chart', chart)
cv2.imshow('chart_canny', chart)

blurred = cv2.GaussianBlur(chart, (5, 5), 2.0)
low = 0
high = 0

def onlow(low_p):
    global low
    low = low_p
    show()

    # rects = cv2.imread('rects.png', cv2.IMREAD_GRAYSCALE)
    # cnts = cv2.findContours(rects, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    # cnts = cnts[0] if len(cnts) == 2 else cnts[1]
    # for cnt in cnts:
    #     approx = cv2.contourArea(cnt)
    #     print(approx)


def onhigh(high_p):
    global high
    high = high_p
    show()


def show():
    global img, low, high
    copy = cv2.Canny(blurred, low, high, None, 5, True)
    cv2.imshow('chart_canny', copy)


cv2.createTrackbar('low', 'chart_canny', 434, 1000, onlow)
cv2.createTrackbar('high', 'chart_canny', 721, 1000, onhigh)

binary = np.ndarray(chart.shape)
binary.fill(0)
binary[chart < 255] = 255
cv2.imwrite('binary.png', binary)
cv2.imshow('binary', binary)

def check(event, x, y, flags, param):
    global chart

    chart_copy = chart.copy()

    if event == cv2.EVENT_MOUSEMOVE:
        print('Pixel = ', chart_copy[y, x])
        if chart_copy.ndim == 3:
            color = 255 - chart_copy[y, x]
            chart_copy[y, :] = color
            chart_copy[:, x] = color

        elif chart_copy.ndim == 2:
            color = 255 - chart_copy[y, x]
            chart_copy[y, :] = color
            chart_copy[:, x] = color
        cv2.imshow('chart', chart_copy)

# cv2.setMouseCallback('chart', check)
# bars = np.ndarray(chart.shape, chart.dtype)
# bars.fill(0)
# bars[(71 <= chart) & (chart <= 108)] = 255
# cv2.imshow('chart_bw', bars)




cv2.waitKey(0)
cv2.destroyAllWindows()
