import cv2
import image_edits as edits
import image_detectations as detects
import to_latex


def main(fname, title_pos):
    print("Main started")
    edits.read(fname)
    print("Read done")

    edits.upscale()
    print("Upscale done")

    edits.treshold()
    print("Treshold done")

    edits.create_binary()
    print("Binary done")

    edits.rotate()
    print("Rotate done")

    detects.connected_components()
    print("Connected done")

    edits.morphological_transform()
    print("Morph done")

    detects.bars()
    print("Bars done")

    detects.define_orientation()
    print("Orientation done")

    # detects.detect_title(title_pos)
    # print("Title done")

    to_latex.latex(False, detects.orientation, detects.ratios, title_pos=title_pos)
    print("Main completed")
    # todo destroyallwindow
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()

# if __name__ == "__main__":
#     # fname = 'chart_ybar.png'
#     fname = 'chart_longtitle.png'
#     main(fname, 1)
