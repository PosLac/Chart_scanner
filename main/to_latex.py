import matplotlib.pyplot as plt
import numpy as np
from pylatex import (Document, TikZ, TikZNode,
                     TikZOptions,
                     Axis, Plot, Command)
import main.image_detectations as detects


def to_latex():
    global orientation, ratios, max_y, new_numbers
    ratios = detects.ratios
    ratios = ratios * (new_numbers[0][5] - 1)
    # todo 5 a max, 4 kell
    x = [1, 2, 3, 4]
    y = ratios

    if orientation == 'xbar':
        y = np.flip(y)
        plt.barh(x, y, 0.25)
    else:
        plt.bar(x, y, 0.25)
    plt.show()

    ratios = ratios / new_numbers[0][5]


orientation = None
ratios = None
max_y = None
chart_title = None
title_below = None


def latex(update, orientation, ratios, minMax_array=None, title=None, title_pos=None):
    print("latex started")
    plot_options = orientation + ", "
    if minMax_array:
        for minMax in minMax_array:
            print(minMax)
            if minMax[2]:
                plot_options = plot_options + minMax[0] + "=" + str(minMax[1]) + ", "

    print("plot_options: ", plot_options)

    if orientation == 'xbar':
        ratios = ratios * detects.r_new_numbers[0][7]
    elif orientation == 'ybar':
        ratios = ratios * detects.c_new_numbers[0][7]

    length = len(ratios)
    doc = Document(documentclass='standalone')

    doc.preamble.append(Command('usetikzlibrary', 'positioning'))

    coordinates = []
    i = 0

    if orientation == 'xbar':
        ratios = np.flip(ratios)
        while i < length:
            coordinates.append((ratios[i], i + 1))
            i += 1

    elif orientation == 'ybar':
        while i < length:
            coordinates.append((i + 1, ratios[i]))
            i += 1

    print("Update: ", update)
    if not update:
        if title_pos == 1:
            detects.chart_title = detects.detect_title(1)
            plot_options = plot_options + 'title=' + detects.chart_title
            print("plot_options: " + plot_options)

        elif title_pos == -1:
            detects.chart_title = detects.detect_title(-1)
            print("title below: " + detects.chart_title)

    else:
        detects.chart_title = title
        if title_pos == 1:
            plot_options = plot_options + 'title=' + detects.chart_title
            print("plot_options: " + plot_options)

        elif title_pos == -1:
            print("title below: " + detects.chart_title)

    with doc.create(TikZ()):
        plot_options = plot_options + ', name=mygraph'
        with doc.create(Axis(options=plot_options)) as plot:
            plot.append(Plot(coordinates=coordinates))

        if title_pos == -1:
            node_chain = TikZNode(text=detects.chart_title, options=TikZOptions('below =of mygraph'))
            doc.append(node_chain)

        with doc.create(TikZNode()) as title:
            title.append(TikZNode())

    doc.generate_pdf('tikzdraw', clean_tex=False, compiler='pdfLaTeX')
