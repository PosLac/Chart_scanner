import cv2


def mouse_click(event, x, y, flags, param):
    # Globalis valtozo atvetele
    global image, clickSwitch, x_click, y_click

    image = image.copy()

    if event == cv2.EVENT_LBUTTONDOWN:
        # print('Pixel = ', x, y)
        if clickSwitch:
            print(
                f"Upper left: [{2 * x_click}, {2 * y_click}], bottom right: [{x}, {y}], "
                f"width: {2 * x - 2 * x_click}, length: {2 * y - 2 * y_click}")

        x_click = x
        y_click = y
        clickSwitch = not clickSwitch

        # (x, y) színérték kiírása
        # print('Pixel = ', image[y, x])

        # Ha 3 csatornás a kép
        # if image.ndim == 3:
        #     # print('R = ', image[y, x, 2])
        #     color = 255 - image[y, x]
        #     image[y, :] = color
        #     image[:, x] = color
        #
        # elif image.ndim == 2:
        #     image[y, :] = 255 - image[y, :]
        cv2.imshow('image', image)


# image_original = cv2.imread('OpenCV-logo.png', cv2.IMREAD_COLOR)
# image_original = cv2.imread('Sudoku_rs.jpg', cv2.IMREAD_COLOR)
# image = cv2.imread('Inputs/chart_xbar.png', cv2.IMREAD_COLOR)
image = cv2.imread('../Inputs/chart_ybar.png', cv2.IMREAD_COLOR)

image = image.copy()
UPSCALE_RATE = 1
width = int(image.shape[1] * UPSCALE_RATE)
height = int(image.shape[0] * UPSCALE_RATE)
image = cv2.resize(image, (width, height))

# image = cv2.imread('OpenCV-logo.png', cv2.IMREAD_GRAYSCALE)
# print('Kép indexelhető dimenziói:', image.ndim)
# print('Kép mérete: ', image.shape)
# print('Kép pixeltípusa: ', image.dtype)

clickSwitch = False
x_click = None
y_click = None
cv2.imshow('image', image)
img_gray = image.copy()
print(cv2.resize(img_gray, (img_gray.shape[0] * 2, img_gray.shape[1] * 2)).shape)
# Egerkezelo callback fuggveny beallitasa az ablakhoz
cv2.setMouseCallback('image', mouse_click)
# Kilepes billentyunyomasra

# while True:
#     key = cv2.waitKey(0)
#     if key == ord('q'):
#         break
#     elif key == ord('r'):
#         image = image_original.copy()
#         cv2.imshow('image', image)

cv2.waitKey(0)
cv2.destroyAllWindows()
