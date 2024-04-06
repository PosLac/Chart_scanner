from functions import image_detections as detects, color_detections, axis_detections
from functions import image_edits as edits
from functions import to_latex
import functions.legend_detections as legend_detections


def main(fname, title_pos, grouped, legend_bars_data=None, legend_position=None):
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

    edits.morphological_transform(detects.chart_with_bars_img, legend_position)
    print("Morph done")

    if grouped:
        legend_detections.detect_legend_position()
        bars_with_colors = color_detections.detect_colors(edits.resized_color, edits.bars_stats, edits.bars_with_labels)
        bars_with_data = color_detections.merge_grouped_chart_bar_colors(bars_with_colors)
        y_axis_type, x_axis_type, y_axis_ticks, x_axis_ticks = axis_detections.define_tick_type_for_axis(title_pos)

        bars_with_text = legend_detections.add_text_to_bars(bars_with_data, legend_bars_data)
        text_for_axis = detects.define_grouped_chart_values(bars_with_text, y_axis_type, x_axis_type, y_axis_ticks,
                                                            x_axis_ticks)
    else:
        simple_bars_with_colors_array = color_detections.detect_colors(edits.resized_color, edits.bars_stats,
                                                                       edits.bars_with_labels)
        color_detections.get_bar_color_for_simple_chart(simple_bars_with_colors_array)
        y_axis_type, x_axis_type, y_axis_ticks, x_axis_ticks = axis_detections.define_tick_type_for_axis(title_pos)
        text_for_axis = detects.define_simple_chart_values(simple_bars_with_colors_array, y_axis_type, x_axis_type,
                                                           y_axis_ticks, x_axis_ticks)

    to_latex.prepare_data_for_generation(detects.orientation, grouped, text_for_axis, legend_bars_data, legend_position,
                                         title_pos=title_pos)
    print("Main completed")
    # todo destroyallwindow
    # cv2.destroyAllWindows()

# functions(fname="chart_ybar.png", title_pos=0)
