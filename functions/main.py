from functions import image_detectations as detects
from functions import image_edits as edits
from functions import to_latex
import functions.detect_legend as legend_detections



def main(fname, title_pos, grouped, bars_with_data=None, legend_position=None):
    """

    Args:
        fname:
        title_pos:
    """
    print("Main started")

    # print(f"Contains legend: {legend is not None}")
    # detects.scan_legend(legend, legend_position)

    edits.read_img(fname)
    print("Read done")

    edits.upscale()
    print("Upscale done")

    edits.ni_black_threshold()
    print("Threshold done")

    edits.threshold()
    print("Binary done")

    edits.rotate()
    print("Rotate done")

    detects.connected_components()
    print("Connected done")

    edits.morphological_transform(detects.chart_with_bars_img, legend_position)
    print("Morph done")

    detects.bars()
    print("Bars done")

    detects.define_orientation()
    print("Orientation done")
    if not grouped:
        colors = detects.detect_colors(edits.resized_color, edits.elements, edits.bars_with_labels)
        detects.bars_with_data = detects.merge_colors(colors)
    else:
        legend_detections.detect_legend_position()
        detects.ratios = [[0, 0.75, 0.5, 0.25], [0.25, 1, 0.25, 0.5]]

    # to_latex.latex(False, detects.orientation, detects.ratios, title_pos=title_pos)
    # to_latex.prepare_data_for_generation(False, detects.orientation, grouped, detects.ratios, bars_with_texts, legend_position) # todo
    # detects.ratios = [[0, 0.75, 0.5, 0.25], [0.25, 1, 0.25, 0.5]]
    to_latex.prepare_data_for_generation(detects.orientation, grouped, detects.ratios, detects.bars_with_data, legend_position, title_pos=title_pos)  # todo
    print("Main completed")
    # todo destroyallwindow
    # cv2.destroyAllWindows()

# functions(fname="chart_ybar.png", title_pos=0)
