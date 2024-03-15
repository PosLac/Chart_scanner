from functions import image_detectations as detects
from functions import to_latex
from functions import image_edits as edits


def main(fname, title_pos, grouped, bars_with_texts=None, legend_position=None):
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

    edits.elements = edits.morphological_transform(detects.chart_with_bars_img)
    print("Morph done")

    detects.detect_colors(edits.resized_color, edits.elements, edits.bars_with_labels)

    detects.bars()
    print("Bars done")

    detects.define_orientation()
    print("Orientation done")

    # to_latex.latex(False, detects.orientation, detects.ratios, title_pos=title_pos)
    # to_latex.prepare_data_for_generation(False, detects.orientation, grouped, detects.ratios, bars_with_texts, legend_position) # todo
    ratios = [[0, 0.75, 0.5, 0.25], [0.25, 1, 0.25, 0.5]]

    to_latex.prepare_data_for_generation(False, "xbar", grouped, ratios, bars_with_texts, legend_position) # todo
    print("Main completed")
    # todo destroyallwindow
    # cv2.destroyAllWindows()


# functions(fname="chart_ybar.png", title_pos=0)
