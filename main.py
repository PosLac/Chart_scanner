import cv2
import image_edits as edits
import image_detectations as detects
import to_latex

if __name__ == "__main__":
    edits.read()
    edits.upscale()
    edits.treshold()
    edits.create_binary()
    edits.rotate()
    detects.connected_components()
    edits.morphological_transform()
    detects.define_orientation()
    # detects.detect_title()
    # to_latex()
    to_latex.latex()
    cv2.waitKey(0)
    cv2.destroyAllWindows()