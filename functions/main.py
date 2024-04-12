from functions import image_detections, color_detections, axis_detections, legend_detections
from functions import image_edits
from functions import to_latex


def main(fname, title_pos, grouped, legend_bars_data=None, legend_position=None):
    print("Main started")

    image_edits.read_img(fname)
    print("Read done")

    image_edits.upscale()
    print("Upscale done")

    image_edits.ni_black_threshold()
    print("Threshold done")

    image_edits.threshold()
    print("Binary done")

    image_edits.rotate()
    print("Rotate done")

    image_edits.morphological_transform(legend_position)
    print("Morph done")

    if grouped:
        legend_detections.detect_legend_position()
        merged_img = color_detections.merge_similar_colors(legend_bars_data)
        bars_with_colors = color_detections.detect_colors_for_grouped_chart(merged_img, legend_bars_data)
        axis_detections.define_tick_type_for_axis(title_pos)
        stacked = image_detections.detect_if_chart_is_stacked(bars_with_colors)

        if stacked:
            image_detections.chart_type = "stacked"
            image_detections.define_stacked_chart_values(bars_with_colors)
        else:
            image_detections.chart_type = "grouped"
            image_detections.define_grouped_chart_values(bars_with_colors)
    else:
        image_detections.chart_type = "simple"
        simple_bars_with_colors_array = color_detections.detect_colors(image_edits.resized_color,
                                                                       image_edits.bars_stats,
                                                                       image_edits.bars_with_labels)
        color_detections.get_bar_color_for_simple_chart(simple_bars_with_colors_array)
        axis_detections.define_tick_type_for_axis(title_pos)
        image_detections.define_simple_chart_values(simple_bars_with_colors_array)

    to_latex.prepare_data_for_generation(image_detections.orientation, image_detections.chart_type, legend_position,
                                         title_pos=title_pos)
    print("Main completed")
