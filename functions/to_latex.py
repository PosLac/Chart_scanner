import numpy as np
from pylatex import (Document, TikZ, TikZNode,
                     TikZOptions,
                     Axis, Plot, Command, NoEscape)

import functions.image_detectations as detects
import functions.detect_legend as legend_detections


# def to_latex():
#     # global orientation, ratios, max_y, new_numbers
#     # ratios = detects.ratios
#     # ratios = ratios * (new_numbers[0][5] - 1)
#     # # todo 5 a max, 4 kell
#     # x = [1, 2, 3, 4]
#     # y = ratios
#     #
#     # if orientation == 'xbar':
#     #     y = np.flip(y)
#     #     plt.barh(x, y, 0.25)
#     # else:
#     #     plt.bar(x, y, 0.25)
#     # plt.show()
#     #
#     # ratios = ratios / new_numbers[0][5]
#     pass  # commented out for global variables issue


# orientation = None
# ratios = None
# max_y = None
# chart_title = None
# title_below = None


# def latex(update, orientation, ratios, minMax_array=None, title=None, title_pos=None):
#     print("latex started")
#     plot_options = orientation + ", "
#     if minMax_array:
#         for minMax in minMax_array:
#             print(minMax)
#             if minMax[2]:
#                 plot_options = plot_options + minMax[0] + "=" + str(minMax[1]) + ", "
#
#     print("plot_options: ", plot_options)
#
#     length = len(ratios)
#     doc = Document(documentclass='standalone')
#
#     doc.preamble.append(Command('usetikzlibrary', 'positioning'))
#
#     coordinates = []
#     i = 0
#
#     if orientation == 'xbar':
#         ratios = np.flip(ratios)
#         while i < length:
#             coordinates.append((ratios[i], i + 1))
#             i += 1
#
#     elif orientation == 'ybar':
#         while i < length:
#             coordinates.append((i + 1, ratios[i]))
#             i += 1
#
#     print("Update: ", update)
#     if not update:
#         if title_pos == 1:
#             detects.chart_title = detects.detect_title(1)
#             plot_options = plot_options + 'title=' + detects.chart_title
#             print("plot_options: " + plot_options)
#
#         elif title_pos == -1:
#             detects.chart_title = detects.detect_title(-1)
#             print("title below: " + detects.chart_title)
#
#     else:
#         detects.chart_title = title
#         if title_pos == 1:
#             plot_options = plot_options + 'title=' + detects.chart_title
#             print("plot_options: " + plot_options)
#
#         elif title_pos == -1:
#             print("title below: " + detects.chart_title)
#
#     with doc.create(TikZ()):
#         plot_options = plot_options + ', name=mygraph'
#         with doc.create(Axis(options=plot_options)) as plot:
#             plot.append(Plot(coordinates=coordinates))
#
#         if title_pos == -1:
#             node_chain = TikZNode(text=detects.chart_title, options=TikZOptions('below =of mygraph'))
#             doc.append(node_chain)
#
#         with doc.create(TikZNode()) as title:
#             title.append(TikZNode())
#
#     doc.generate_pdf('tikzdraw', clean_tex=False, compiler='pdfLaTeX')

# def latex_with_legend(update, orientation, ratios, bars_with_texts=None, minMax_array=None, title=None, title_pos=None):
#     print("latex started")
#     plot_options = orientation + ", "
#     if minMax_array:
#         for minMax in minMax_array:
#             print(minMax)
#             if minMax[2]:
#                 plot_options = plot_options + minMax[0] + "=" + str(minMax[1]) + ", "
#
#     print("plot_options: ", plot_options)
#
#     # if orientation == 'xbar':
#     #     ratios = ratios * detects.r_new_numbers[0][7]
#     # elif orientation == 'ybar':
#     #     ratios = ratios * detects.c_new_numbers[0][7]
#
#     length = len(ratios)
#     doc = Document(documentclass='standalone')
#
#     doc.preamble.append(Command('usetikzlibrary', 'positioning'))
#
#     coordinates = []
#     i = 0
#
#     if orientation == 'xbar':
#         ratios = np.flip(ratios)
#         while i < length:
#             coordinates.append((ratios[i], i + 1))
#             i += 1
#
#     elif orientation == 'ybar':
#         while i < length:
#             coordinates.append((i + 1, ratios[i]))
#             i += 1
#
#     # print("Update: ", update)
#     # if not update:
#     #     if title_pos == 1:
#     #         detects.chart_title = detects.detect_title(1)
#     #         plot_options = plot_options + 'title=' + detects.chart_title
#     #         print("plot_options: " + plot_options)
#     #
#     #     elif title_pos == -1:
#     #         detects.chart_title = detects.detect_title(-1)
#     #         print("title below: " + detects.chart_title)
#     #
#     # else:
#     #     detects.chart_title = title
#     #     if title_pos == 1:
#     #         plot_options = plot_options + 'title=' + detects.chart_title
#     #         print("plot_options: " + plot_options)
#     #
#     #     elif title_pos == -1:
#     #         print("title below: " + detects.chart_title)
#
#     colors = []
#     texts = []
#     for key, values in bars_with_texts.items():
#         colors.append(values["bar_color"])
#         texts.append(values["text"])
#
#     with doc.create(TikZ()):
#         plot_options = plot_options + ', name=mygraph'
#         with doc.create(Axis(options=plot_options)) as plot:
#             plot.append(Plot(coordinates=coordinates, options=NoEscape('color=rgb,rgb=(0, 1, 1)')))
#
#         if title_pos == -1:
#             node_chain = TikZNode(text=detects.chart_title, options=TikZOptions('below =of mygraph'))
#             doc.append(node_chain)
#
#         with doc.create(TikZNode()) as title:
#             title.append(TikZNode())
#
#     doc.generate_pdf('tikzdraw', clean_tex=False, compiler='pdfLaTeX')

#
# def prepare_data_for_generation(update, orientation, grouped, ratios, bars_with_texts=None, min_max_array=None,
#                                 title=None, title_pos=None):
#     plot_options = orientation + ', name=mygraph'
#     legend_arguments = ""
#     define_color_arguments = []
#     coordinates_with_options = []
#
#     if orientation == 'xbar':
#         m = detects.r_new_numbers[0][7]
#     else:
#         m = detects.c_new_numbers[0][7]
#
#     if grouped:
#         if orientation == 'xbar':
#             for i in range(len(ratios)):
#                 ratios[i] = np.flip(ratios[i])
#         for i in range(len(ratios)):
#             ratios[i] *= m
#     else:
#         if orientation == 'xbar':
#             ratios = np.flip(ratios)
#             ratios *= m
#     print(f"ratios: {ratios}")
#
#     for key, values in bars_with_texts.items():
#         color_str = ", ".join(map(str, values["bar_color"]))
#         define_color_arguments.append(["color" + str(key + 1), "RGB", color_str])
#         legend_arguments = ", ".join(value["text"] for key, value in bars_with_texts.items())
#     print(f"legend_arguments: {legend_arguments}")
#     print(f"define_color_arguments: {define_color_arguments}")
#
#     for group_index in range(len(ratios)):
#         group = ratios[group_index]
#         group_coordinates = []
#         for bar_index in range(len(group)):
#             if orientation == "xbar":
#                 group_coordinates.append((group[bar_index], bar_index + 1))
#             else:
#                 group_coordinates.append((bar_index + 1, group[bar_index]))
#         coordinates_with_options.append((group_coordinates, f'fill=color{group_index + 1}'))
#     print(f"group_coordinates: {coordinates_with_options}")
#
#     if min_max_array:
#         for min_max in min_max_array:
#             print(min_max)
#             if min_max[2]:
#                 plot_options = plot_options + min_max[0] + "=" + str(min_max[1]) + ", "
#     print(f"plot_options: {plot_options}")
#
#     # print("Update: ", update)
#     # if not update:
#     #     if title_pos == 1:
#     #         detects.chart_title = detects.detect_title(1)
#     #         plot_options = plot_options + 'title=' + detects.chart_title
#     #         print("plot_options: " + plot_options)
#     #
#     #     elif title_pos == -1:
#     #         detects.chart_title = detects.detect_title(-1)
#     #         print("title below: " + detects.chart_title)
#     #
#     # else:
#     #     detects.chart_title = title
#     #     if title_pos == 1:
#     #         plot_options = plot_options + 'title=' + detects.chart_title
#     #         print("plot_options: " + plot_options)
#     #
#     #     elif title_pos == -1:
#     #         print("title below: " + detects.chart_title)
#
#     generate_latex_with_legend(plot_options, legend_arguments, define_color_arguments, coordinates_with_options)


def prepare_data_for_generation(orientation, grouped, ratios, bars_with_data=None, legend_position=None, title=None, title_pos=None):
    print("\tPrepare data for generation")
    if bars_with_data is None:
        bars_with_data = {
            0: {'color': [179, 179, 255], 'bar_x': 21, 'bar_y': 18, 'bar_w': 36, 'bar_h': 40, 'text': 'Label-1'},
            1: {'color': [253, 180, 181], 'bar_x': 21, 'bar_y': 70, 'bar_w': 36, 'bar_h': 40, 'text': 'Label-2'}
        }
    plot_options_array = [orientation, 'name=mygraph']
    define_color_arguments = []
    coordinates_with_options = []

    # set options to title above the chart
    plot_options_array = prepare_title_above(False, plot_options_array, title, title_pos)

    max_number = detects.tick_number_of_longest_bar
    print(f"\tmax_number: {max_number}")

    # set options for grouped chart
    if grouped:
        ratios, plot_options_array, define_color_arguments, legend_arguments = prepare_data_for_grouped_chart(True,
                                                                                                              plot_options_array,
                                                                                                              orientation,
                                                                                                              ratios,
                                                                                                              legend_position,
                                                                                                              bars_with_data,
                                                                                                              define_color_arguments,
                                                                                                              coordinates_with_options)
    else:
        if orientation == 'xbar':
            ratios = np.flip(ratios)
        ratios *= max_number

        coordinates = []
        for bar_index in range(len(ratios)):
            if orientation == "xbar":
                coordinates.append((round(ratios[bar_index], 2), bar_index + 1))
            else:
                coordinates.append((bar_index + 1, round(ratios[bar_index], 2)))
        coordinates_with_options.append((coordinates, 'fill=color'))
        color_str = ", ".join(map(str, detects.simple_chart_bar_color))
        define_color_arguments.append(["color", "RGB", color_str])
        legend_arguments = ""

        # for key, values in bars_with_data.items():
        #     color_str = ", ".join(map(str, values["color"]))
        #     define_color_arguments.append(["color" + str(key + 1), "RGB", color_str])

    print(f"\tratios: {ratios}")
    print(f"\tdefine_color_arguments: {define_color_arguments}")
    print(f"\tgroup_coordinates: {coordinates_with_options}")

    plot_options_str = ", ".join(plot_options_array)

    generate_latex(plot_options_str, legend_arguments, define_color_arguments, coordinates_with_options, title,
                   title_pos)


def prepare_data_for_update(orientation, grouped, updated_ratios, color, bars_with_data=None, legend_position=None, min_max_array=None, title=None, title_pos=None):
    legend_arguments = ""
    plot_options_array = [orientation, 'name=mygraph']
    define_color_arguments = []
    coordinates_with_options = []

    # set options to title above the chart
    plot_options_array = prepare_title_above(True, plot_options_array, title, title_pos)

    # set minimum and maximum values for x and y-axis
    if min_max_array:
        print(f"\tmin_max_array: {min_max_array}")
        for min_max in min_max_array:
            if min_max[2]:
                plot_options_array.append(min_max[0] + "=" + str(min_max[1]))

    # set options for grouped chart
    if grouped:
        updated_ratios, plot_options_array, define_color_arguments, legend_arguments = prepare_data_for_grouped_chart(True,
                                                                                                                      plot_options_array,
                                                                                                                      orientation,
                                                                                                                      updated_ratios,
                                                                                                                      legend_position,
                                                                                                                      bars_with_data,
                                                                                                                      define_color_arguments,
                                                                                                                      coordinates_with_options)

    else:
        if orientation == 'xbar':
            updated_ratios = np.flip(updated_ratios)

        coordinates = []
        for bar_index in range(len(updated_ratios)):
            if orientation == "xbar":
                coordinates.append((round(updated_ratios[bar_index], 2), bar_index + 1))
            else:
                coordinates.append((bar_index + 1, round(updated_ratios[bar_index], 2)))
        coordinates_with_options.append((coordinates, f'fill=color{1}'))

        color_str = ", ".join(map(str, color))
        define_color_arguments.append(["color1", "RGB", color_str])

    print(f"\tratios: {updated_ratios}")
    print(f"\tdefine_color_arguments: {define_color_arguments}")
    print(f"\tgroup_coordinates: {coordinates_with_options}")

    plot_options_str = ", ".join(plot_options_array)

    generate_latex(plot_options_str, legend_arguments, define_color_arguments, coordinates_with_options, title,
                   title_pos)


def prepare_data_for_grouped_chart(update, plot_options_array, orientation, ratios, legend_position, bars_with_data, define_color_arguments, coordinates_with_options):
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
    print(f"\tplot_options: {plot_options_array}")

    if orientation == 'xbar':
        for i in range(len(ratios)):
            ratios[i] = np.flip(ratios[i])
            if update:
                ratios[i] *= detects.r_new_numbers[0][7]

    for key, values in bars_with_data.items():
        color_str = ", ".join(map(str, values["color"]))
        define_color_arguments.append(["color" + str(key + 1), "RGB", color_str])
        legend_arguments = ", ".join(value["text"] for key, value in bars_with_data.items())

    print(f"\tlegend_arguments: {legend_arguments}")

    for group_index in range(len(ratios)):
        group = ratios[group_index]
        # print(f"group: {group}")
        group_coordinates = []
        for bar_index in range(len(group)):
            if orientation == "xbar":
                group_coordinates.append((group[bar_index], bar_index + 1))
            else:
                group_coordinates.append((bar_index + 1, group[bar_index]))
        coordinates_with_options.append((group_coordinates, f'fill=color{group_index + 1}'))

    return ratios, plot_options_array, define_color_arguments, legend_arguments


def prepare_title_above(update, plot_options_array, title, title_pos):

    if update:
        # title above the chart
        if title_pos == 1:
            detects.chart_title = title
            plot_options_array.append('title=' + title)

        # title below the chart
        elif title_pos == -1:
            detects.chart_title = title

    else:
        # title above the chart
        if title_pos == 1:
            detects.chart_title = detects.detect_title(1)
            plot_options_array.append('title=' + detects.chart_title)

        # title below the chart
        elif title_pos == -1:
            detects.chart_title = detects.detect_title(-1)

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
            # insert legend
            if legend_arguments != "":
                plot.append(Command("legend", arguments=NoEscape(legend_arguments)))

        # insert title below the chart
        if title_pos == -1:
            node_chain = TikZNode(text=title, options=TikZOptions('below =of mygraph'))
            doc.append(node_chain)

    doc.generate_pdf('tikzdraw', clean_tex=False, compiler='pdfLaTeX')
    print("Latex generation finished")
