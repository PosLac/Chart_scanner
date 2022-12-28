import matplotlib.pyplot as plt
import numpy as np
from pylatex import (Document, TikZ, TikZNode,
                     TikZOptions,
                     Axis, Plot, Package, Command)
import image_detectations as detects

def to_latex():
    global orientation, ratios, max_y, new_numbers
    ratios = detects.ratios
    ratios = ratios * (new_numbers[0][5] - 1)
    # todo 5 a max, 4 kell
    x = [1, 2, 3, 4]
    y = ratios

    if orientation == 'xbar':
        y = np.flip(y)
        # y = sorted(y, reverse=True)
        plt.barh(x, y, 0.25)
    else:
        plt.bar(x, y, 0.25)

    # plt.title()
    # plt.xlabel()
    # plt.ylabel()
    plt.show()

    ratios = ratios / new_numbers[0][5]


def latex():
    global orientation, ratios, max_y, new_numbers, chart_title, title_below
    ratios = detects.ratios
    orientation = detects.orientation
    if orientation == 'xbar':
        ratios = ratios * detects.r_new_numbers[0][7]
    elif orientation == 'ybar':
        ratios = ratios * detects.c_new_numbers[0][7]

    print('coordinates: ', ratios)
    # todo 5 a max, 4 kell
    length = len(ratios)
    doc = Document()

    # doc.packages.append(Package('fontspec'))
    # doc.packages.append(Package('sansmath'))
    doc.preamble.append(Command('usetikzlibrary', 'positioning'))

    coordinates = []
    i = 0

    if orientation == 'xbar':
        ratios = np.flip(ratios)
        while i < length:
            coordinates.append((ratios[i], i + 1))
            i += 1

    elif orientation == 'ybar':
        # ratios = np.flip(ratios)
        while i < length:
            # coordinates.append((ratios[i], i+1))
            coordinates.append((i + 1, ratios[i]))
            i += 1

    print(coordinates)

    title_string = ''
    title_below = False
    chart_title = detects.detect_title()
    print(chart_title)
    if not title_below:
        title_string = ', title = ' + chart_title


    with doc.create(TikZ()):
        # plot_options = orientation + ', title style={align=left}, ymin = 0, ymax = 9, xmin = 0, xmax = 9'
        plot_options = orientation + ', name=mygraph' + title_string \
                       + ', xmin = ' + str(detects.c_new_numbers[-1][7])\
                       + ', xmax = ' + str(detects.c_new_numbers[0][7])\
                       + ', ymin = ' + str(detects.r_new_numbers[-1][7])\
                       + ', ymax = ' + str(detects.r_new_numbers[0][7])

        # plot_options = orientation + ', name=mygraph' + title_string
        with doc.create(Axis(options=plot_options)) as plot:
            plot.append(Plot(coordinates=coordinates))

        if title_below:
            node_chain = TikZNode(text=str('Diagramcím'),
                                  options=TikZOptions('below =of mygraph'))
            doc.append(node_chain)

        with doc.create(TikZNode()) as title:
            title.append(TikZNode())

    doc.generate_pdf('tikzdraw', clean_tex=False, compiler='pdfLaTeX')