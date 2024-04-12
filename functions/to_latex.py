from pylatex import (Document, TikZ, TikZNode,
                     TikZOptions,
                     Axis, Plot, Command, NoEscape)

import functions.image_detections as detects
import functions.legend_detections as legend_detections
from functions import axis_detections, image_detections


def prepare_universal_data(orientation, chart_type, bgr_color_data, title, legend_position=None,
                           title_pos=None):
    print("\tPrepare universal data")
    plot_options_array = [orientation, "name=barchart"]
    define_color_arguments = []
    coordinates_with_options = []
    axis_types_with_ticks = axis_detections.axis_types_with_ticks

    # Set options to title above the chart
    plot_options_array = prepare_title(plot_options_array, title, title_pos)

    # Set text ticks
    if image_detections.text_for_axis:
        if orientation == "xbar":
            image_detections.text_for_axis = image_detections.text_for_axis[::-1]

        plot_options_array.append("symbolic " + ("x" if orientation == "ybar" else "y") + " coords={" + ", ".join(
            ["{" + t['value'] + "}" for t in image_detections.text_for_axis]) + "}")

        if orientation == "xbar":
            plot_options_array.append("ytick=data")
        else:
            plot_options_array.append("xtick=data")

    # Set options for grouped chart
    if chart_type == "grouped":
        plot_options_array, define_color_arguments, legend_arguments, coordinates_with_options = prepare_data_for_grouped_chart(
            plot_options_array,
            legend_position,
            bgr_color_data)

    # Set options for stacked chart
    elif chart_type == "stacked":

        plot_options_array[0] = orientation + " stacked"

        plot_options_array, define_color_arguments, legend_arguments, coordinates_with_options = prepare_data_for_grouped_chart(
            plot_options_array,
            legend_position,
            bgr_color_data)

    # Set options for simple chart
    else:
        coordinates = []
        for bar in detects.bars_with_axis_value_pairs:
            coordinates.append(("{" + str(bar["row value"]) + "}", "{" + str(bar["column value"]) + "}"))
        coordinates_with_options.append((coordinates, "fill=color"))
        color_str = ", ".join(map(str, bgr_color_data[::-1]))
        define_color_arguments.append(["color", "RGB", color_str])
        legend_arguments = ""

    # Set minimum and maximum ticks for y-axis
    if axis_types_with_ticks["y_axis_type"] == "number":
        plot_options_array.append(f"ymin={axis_types_with_ticks['y_axis_min']}")
        plot_options_array.append(f"ymax={axis_types_with_ticks['y_axis_max']}")

    # Set minimum and maximum ticks for x-axis
    if axis_types_with_ticks["x_axis_type"] == "number":
        plot_options_array.append(f"xmin={axis_types_with_ticks['x_axis_min']}")
        plot_options_array.append(f"xmax={axis_types_with_ticks['x_axis_max']}")

    return plot_options_array, define_color_arguments, legend_arguments, coordinates_with_options


def prepare_data_for_generation(orientation, chart_type, legend_position=None, title_pos=None):
    print("\tPrepare data for generation")

    plot_options_array, define_color_arguments, legend_arguments, coordinates_with_options = prepare_universal_data(
        orientation, chart_type, image_detections.colors, image_detections.title, legend_position, title_pos)

    image_detections.print_array("define_color_arguments", define_color_arguments)
    image_detections.print_array("group_coordinates", coordinates_with_options)

    plot_options_str = ", ".join(plot_options_array)

    generate_latex(plot_options_str, legend_arguments, define_color_arguments, coordinates_with_options,
                   image_detections.title, title_pos)


def prepare_data_for_update(orientation, chart_type, colors, legend_position=None, title=None,
                            title_pos=None):
    print("\tPrepare data for update")

    plot_options_array, define_color_arguments, legend_arguments, coordinates_with_options = prepare_universal_data(
        orientation, chart_type, colors, title, legend_position, title_pos)

    image_detections.print_array("define_color_arguments", define_color_arguments)
    image_detections.print_array("group_coordinates", coordinates_with_options)

    plot_options_str = ", ".join(plot_options_array)

    generate_latex(plot_options_str, legend_arguments, define_color_arguments, coordinates_with_options, title,
                   title_pos)


def prepare_data_for_grouped_chart(plot_options_array, legend_position, texts_and_colors):
    define_color_arguments = []
    coordinates_with_options = []
    top_right_point = legend_detections.top_right_point
    bottom_left_point = legend_detections.bottom_left_point

    width = top_right_point[0] - bottom_left_point[0]
    height = bottom_left_point[1] - top_right_point[1]

    legend_arguments = ""
    legend_top_right_orig = legend_position.topRight()

    from_x = min(round(1 - (top_right_point[0] - legend_top_right_orig.x()) / width, 2), 1)
    from_y = min(round(1 - (legend_top_right_orig.y() - top_right_point[1]) / height, 2), 1)

    legend_top_right = from_x, from_y
    plot_options_array.append("legend style={at={" + str(legend_top_right) + "}}")
    plot_options_array.append("legend cell align={left}")
    image_detections.print_array("plot_options", plot_options_array)

    # First generation
    if isinstance(texts_and_colors, list):
        for i, bar in enumerate(texts_and_colors):
            color_str = ", ".join(map(str, bar["bgr_color"][::-1]))
            define_color_arguments.append(["color" + str(i + 1), "RGB", color_str])
            legend_arguments = ", ".join(bar["text"] for bar in texts_and_colors)
    else:
        for i, (key, value) in enumerate(texts_and_colors.items()):
            color_str = ", ".join(map(str, value[::-1]))
            define_color_arguments.append(["color" + str(i + 1), "RGB", color_str])
        legend_arguments = ", ".join(texts_and_colors.keys())

    print(f"\tlegend_arguments: {legend_arguments}")

    bias = []
    length = len(detects.bars_with_axis_value_pairs.values())
    center = length // 2

    if length % 2 == 0:
        for i in range(length):
            bias.append((i - center) * 24 + 24 / 2)
    else:
        for i in range(-center, center + 1):
            bias.append(i * 24)

    for i, value in enumerate(detects.bars_with_axis_value_pairs.values()):
        group_coordinates = []
        for bar in value["bars"]:
            group_coordinates.append((bar["row value"], bar["column value"]))
        coordinates_with_options.append((group_coordinates, f"fill=color{i + 1}"))

    return plot_options_array, define_color_arguments, legend_arguments, coordinates_with_options


def prepare_title(plot_options_array, title, title_pos):
    # Title above the chart
    if title_pos == 1:
        detects.chart_title = title
        plot_options_array.append('title=' + title)

    # Title below the chart
    elif title_pos == -1:
        detects.chart_title = title

    return plot_options_array


def generate_latex(plot_options, legend_arguments, define_color_arguments, coordinates_with_options, title, title_pos):
    print("Latex generation started")

    doc = Document(documentclass='standalone')
    doc.preamble.append(Command('usetikzlibrary', 'positioning'))

    with doc.create(TikZ()) as tikz:
        for arguments in define_color_arguments:
            tikz.append(Command("definecolor", arguments=arguments))

        with doc.create(Axis(options=NoEscape(plot_options))) as plot:
            for (coordinates, options) in coordinates_with_options:
                plot.append(Plot(coordinates=coordinates, options=NoEscape(options)))
            # Insert legend
            if legend_arguments != "":
                plot.append(Command("legend", arguments=NoEscape(legend_arguments)))

        # Insert title below the chart
        if title_pos == -1:
            node_chain = TikZNode(text=title, options=TikZOptions('below =of barchart'))
            doc.append(node_chain)

    doc.generate_pdf('tikzdraw', clean_tex=False, compiler='pdfLaTeX')
    print("Latex generation finished")
