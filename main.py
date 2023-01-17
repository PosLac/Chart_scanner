import cv2
import image_edits as edits
import image_detectations as detects
import to_latex

def main(fname):
    print("Main started")
    edits.read(fname)
    edits.upscale()
    edits.treshold()
    edits.create_binary()
    edits.rotate()
    detects.connected_components()
    edits.morphological_transform()
    detects.bars()
    detects.define_orientation()
    # 0: nincs
    # 1: felül
    # -1: alul
    detects.detect_title(0)
    # to_latex()
    to_latex.latex(detects.orientation, detects.ratios)
    print("Main completed")
    # todo destroyallwindow
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()


# if __name__ == "__main__":
#     fname = 'chart_xbar.png'
#     main(fname)
