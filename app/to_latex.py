from datetime import datetime
from typing import Tuple, Union

from PyQt5.QtCore import QRect
from pylatex import (Document, TikZ, TikZNode,
                     TikZOptions,
                     Axis, Plot, Command, NoEscape)

from app import axis_detections, image_detections, legend_detections
from config import config

DEFAULT_LEGEND_POSITION = 0.95
logger = config.logger


def prepare_universal_data(chart_type: str, bgr_color_data: Union[dict, list], title: str, legend_position: QRect = None, title_pos: int = None) -> Tuple[list, list, str, list]:
    """
    Prepares data and options for latex generation and updae

    Args:
        chart_type:     type of the chart ("simple" or "grouped" or "stacked")
        bgr_color_data: bgr colors of bars
        title:          detected title
        legend_position:    QRect of the cropped area for legend
        title_pos:          position of the title to detect (-1: below, 0: no title, 1: above)

    Returns:
        plot_options_array:     latex options for the chart
        define_color_arguments: custom color arguments in latex format
        legend_arguments:       arguments for the legend in latex format
        coordinates_with_options:   coordinates for the chart in latex format
    """
    logger.info("Prepare universal data")
    plot_options_array = [image_detections.orientation, "name=barchart"]
    define_color_arguments = []
    coordinates_with_options = []
    axis_types_with_ticks = axis_detections.axis_types_with_ticks

    # Set options to title above the chart
    plot_options_array = prepare_title(plot_options_array, title, title_pos)

    # Set text ticks
    if image_detections.text_for_axis:
        if image_detections.orientation == "xbar":
            plot_options_array.append(
                "symbolic " + ("x" if image_detections.orientation == "ybar" else "y") + " coords={" + ", ".join(
                    ["{" + t['value'] + "}" for t in image_detections.text_for_axis][::-1]) + "}")

        elif image_detections.orientation == "ybar":
            plot_options_array.append(
                "symbolic " + ("x" if image_detections.orientation == "ybar" else "y") + " coords={" + ", ".join(
                    ["{" + t['value'] + "}" for t in image_detections.text_for_axis]) + "}")

        if image_detections.orientation == "xbar":
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

        plot_options_array[0] = image_detections.orientation + " stacked"

        plot_options_array, define_color_arguments, legend_arguments, coordinates_with_options = prepare_data_for_grouped_chart(
            plot_options_array,
            legend_position,
            bgr_color_data)

    # Set options for simple chart
    else:
        coordinates = []
        for bar in image_detections.bars_with_axis_value_pairs:
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


def prepare_data_for_generation(chart_type: str, legend_position: QRect = None, title_pos: int = None) -> None:
    """
    Prepares data and options for latex generation

    Args:
        chart_type: type of the chart ("simple" or "grouped" or "stacked")
        chart_type:     type of the chart ("simple" or "grouped" or "stacked")
        legend_position:    QRect of the cropped area for legend
        title_pos:          position of the title to detect (-1: below, 0: no title, 1: above)

    Returns:
        None
    """
    logger.info("Prepare data for generation")

    plot_options_array, define_color_arguments, legend_arguments, coordinates_with_options = prepare_universal_data(
        chart_type, image_detections.colors, image_detections.title, legend_position, title_pos)

    plot_options_str = ", ".join(plot_options_array)

    current_date_time_str = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    config.file_name = str(chart_type + "_" + image_detections.orientation + "_" + current_date_time_str)

    generate_latex(plot_options_str, legend_arguments, define_color_arguments, coordinates_with_options,
                   image_detections.title, title_pos)


def prepare_data_for_update(chart_type: str, colors: list, legend_position: QRect = None, title: str = None, title_pos: int = None) -> None:
    """
    Prepares data and options for update latex code

    Args:
        chart_type:     type of the chart ("simple" or "grouped" or "stacked")
        colors:     colors of the bars to update
        legend_position:    QRect of the cropped area for legend
        title:  title text to update
        title_pos:      position of the title to update (-1: below, 0: no title, 1: above)

    Returns:
        None
    """
    logger.info("Prepare data for update")

    plot_options_array, define_color_arguments, legend_arguments, coordinates_with_options = prepare_universal_data(
        chart_type, colors, title, legend_position, title_pos)

    plot_options_str = ", ".join(plot_options_array)

    generate_latex(plot_options_str, legend_arguments, define_color_arguments, coordinates_with_options, title,
                   title_pos)


def prepare_data_for_grouped_chart(plot_options_array: list, legend_position: QRect, texts_and_colors: dict) -> Tuple[list, list, str, list]:
    """
    Prepares data and options for grouped charts to generate latex code

    Args:
        plot_options_array: latex options for the chart
        legend_position:    QRect of the cropped area for legend
        texts_and_colors:   bar texts and colors

    Returns:
        plot_options_array:     latex options for the chart
        define_color_arguments: custom color arguments in latex format
        legend_arguments:       arguments for the legend in latex format
        coordinates_with_options:   coordinates for the chart in latex format
    """
    legend_arguments = ""
    define_color_arguments = []
    coordinates_with_options = []

    if len(legend_detections.chart_border_polygon_resized) == 0:
        legend_top_right = DEFAULT_LEGEND_POSITION, DEFAULT_LEGEND_POSITION
    else:
        top_right_point = legend_detections.chart_border_polygon_resized[1]
        bottom_left_point = legend_detections.chart_border_polygon_resized[3]

        width = top_right_point[0] - bottom_left_point[0]
        height = bottom_left_point[1] - top_right_point[1]

        if width == 0 or height == 0:
            legend_top_right = DEFAULT_LEGEND_POSITION, DEFAULT_LEGEND_POSITION
        else:
            legend_top_right_orig = legend_position.topRight()

            from_x = min(round(1 - (top_right_point[0] - legend_top_right_orig.x()) / width, 2), 1)
            from_y = min(round(1 - (legend_top_right_orig.y() - top_right_point[1]) / height, 2), 1)

            if not 0 < from_x < 1:
                from_x = DEFAULT_LEGEND_POSITION

            if not 0 < from_y < 1:
                from_y = DEFAULT_LEGEND_POSITION

            legend_top_right = from_x, from_y
    logger.info(f"Detected legend position: {str(legend_arguments)}")

    plot_options_array.append("legend style={at={" + str(legend_top_right) + "}}")
    plot_options_array.append("legend cell align={left}")

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

    logger.info(f"legend_arguments: [{legend_arguments}]")

    bias = []
    length = len(image_detections.bars_with_axis_value_pairs.values())
    center = length // 2

    if length % 2 == 0:
        for i in range(length):
            bias.append((i - center) * 24 + 24 / 2)
    else:
        for i in range(-center, center + 1):
            bias.append(i * 24)

    for i, value in enumerate(image_detections.bars_with_axis_value_pairs.values()):
        group_coordinates = []
        for bar in value["bars"]:
            group_coordinates.append((bar["row value"], bar["column value"]))
        coordinates_with_options.append((group_coordinates, f"fill=color{i + 1}"))

    return plot_options_array, define_color_arguments, legend_arguments, coordinates_with_options


def prepare_title(plot_options_array: list, title: str, title_pos: int) -> list:
    """
    Prepare title options for latex generation

    Args:
        plot_options_array: latex options for the chart
        title:  text of the chart title
        title_pos:  position of the title to detect (-1: below, 0: no title, 1: above)

    Returns:
        plot_options_array: latex options for the chart completed by title
    """
    # Title above the chart
    if title_pos == 1:
        image_detections.chart_title = title
        plot_options_array.append('title=' + title)

    # Title below the chart
    elif title_pos == -1:
        image_detections.chart_title = title

    return plot_options_array


def generate_latex(plot_options_str: str, legend_arguments: str, define_color_arguments: list, coordinates_with_options: list, title: str, title_pos: int) -> None:
    """
    Generate latex code from the given options

    Args:
        plot_options_str:   latex options for the chart
        legend_arguments:   arguments for the legend
        define_color_arguments:     arguments for the custom colors
        coordinates_with_options:   coordinates and their options
        title:      text of the title
        title_pos:  position of the title to detect (-1: below, 0: no title, 1: above)

    Returns:
        None

    Raises:
        PyLaTeXError:   if exception raised during latex file generation
        CalledProcessError: if latex generation returns with non-zero value
    """
    logger.info("Latex file generation started")

    doc = Document(documentclass="standalone")
    doc.preamble.append(Command("usetikzlibrary", "positioning"))

    with doc.create(TikZ()) as tikz:
        for arguments in define_color_arguments:
            tikz.append(Command("definecolor", arguments=arguments))

        with doc.create(Axis(options=NoEscape(plot_options_str))) as plot:
            for (coordinates, options) in coordinates_with_options:
                plot.append(Plot(coordinates=coordinates, options=NoEscape(options)))
            # Insert legend
            if legend_arguments != "":
                plot.append(Command("legend", arguments=NoEscape(legend_arguments)))

        # Insert title below the chart
        if title_pos == -1:
            node_chain = TikZNode(text=title, options=TikZOptions('below =of barchart'))
            doc.append(node_chain)

    doc.generate_pdf(str(config.generated_charts_path / config.file_name), clean_tex=False, compiler="pdfLaTeX")
    logger.info("Latex file generation finished")
