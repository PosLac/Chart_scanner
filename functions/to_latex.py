from pylatex import (Document, TikZ, TikZNode,
                     TikZOptions,
                     Axis, Plot, Command, NoEscape)

import functions.image_detections as detects
import functions.legend_detections as legend_detections
from functions import axis_detections, image_detections


def prepare_data_for_generation(orientation, grouped, texts_for_axis=None, legend_bars_with_data=None,
                                legend_position=None, title_pos=None):
    print("\tPrepare data for generation")

    plot_options_array = [orientation, 'name=mygraph']
    define_color_arguments = []
    coordinates_with_options = []

    # Set options to title above the chart
    plot_options_array = prepare_title(plot_options_array, image_detections.title, title_pos)

    if texts_for_axis:
        texts_for_axis = texts_for_axis[::-1]
        plot_options_array.append("symbolic " + ("x" if orientation == "ybar" else "y") + " coords={" + ", ".join(
            ["{" + t['value'] + "}" for t in texts_for_axis]) + "}")

    max_number = axis_detections.longest_bar_value
    print(f"\ttick_number_of_longest_bar: {max_number}")

    # Set options for grouped chart
    if grouped:
        plot_options_array, define_color_arguments, legend_arguments, coordinates_with_options = prepare_data_for_grouped_chart(
            plot_options_array,
            legend_position,
            legend_bars_with_data)
    else:
        coordinates = []
        for bar in detects.bars_with_axis_value_pairs:
            coordinates.append(("{" + str(bar["row value"]) + "}", "{" + str(bar["column value"]) + "}"))
        coordinates_with_options.append((coordinates, 'fill=color'))
        color_str = ", ".join(map(str, image_detections.colors))
        define_color_arguments.append(["color", "RGB", color_str])
        legend_arguments = ""

    print(f"\tdefine_color_arguments: {define_color_arguments}")
    print(f"\tgroup_coordinates: {coordinates_with_options}")

    plot_options_str = ", ".join(plot_options_array)

    generate_latex(plot_options_str, legend_arguments, define_color_arguments, coordinates_with_options,
                   image_detections.title, title_pos)


def prepare_data_for_update(orientation, grouped, updated_ratios, color_data, legend_position=None, min_max_array=None,
                            title=None, title_pos=None):
    legend_arguments = ""
    plot_options_array = [orientation, 'name=mygraph']
    define_color_arguments = []
    coordinates_with_options = []

    # Set options to title above the chart
    plot_options_array = prepare_title(plot_options_array, title, title_pos)

    # Set minimum and maximum values for x and y-axis
    if min_max_array:
        print(f"\tmin_max_array: {min_max_array}")
        for min_max in min_max_array:
            if min_max[2]:
                plot_options_array.append(min_max[0] + "=" + str(min_max[1]))

    # Set options for grouped chart
    if grouped:
        plot_options_array, define_color_arguments, legend_arguments, coordinates_with_options = prepare_data_for_grouped_chart(
            plot_options_array, legend_position, color_data)

    else:
        coordinates = []
        for bar in detects.bars_with_axis_value_pairs:
            if orientation == "xbar":
                coordinates.append((bar["row value"], bar["column value"]))
            else:
                coordinates.append((bar["column value"], bar["row value"]))

        coordinates_with_options.append((coordinates, f'fill=color{1}'))

        color_str = ", ".join(map(str, color_data))
        define_color_arguments.append(["color1", "RGB", color_str])

    print(f"\tratios: {updated_ratios}")
    print(f"\tdefine_color_arguments: {define_color_arguments}")
    print(f"\tgroup_coordinates: {coordinates_with_options}")

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
    print(f"\tplot_options: {plot_options_array}")

    # First generation
    if isinstance(texts_and_colors, list):
        for i, bar in enumerate(texts_and_colors):
            color_str = ", ".join(map(str, bar["color"]))
            define_color_arguments.append(["color" + str(i + 1), "RGB", color_str])
            legend_arguments = ", ".join(bar["text"] for bar in texts_and_colors)
    else:
        for i, (key, value) in enumerate(texts_and_colors.items()):
            color_str = ", ".join(map(str, value))
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
            node_chain = TikZNode(text=title, options=TikZOptions('below =of mygraph'))
            doc.append(node_chain)

    doc.generate_pdf('tikzdraw', clean_tex=False, compiler='pdfLaTeX')
    print("Latex generation finished")
