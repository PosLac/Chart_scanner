import cv2

from app import image_detections, color_detections, axis_detections, legend_detections
from app import image_edits
from app import to_latex
from main import logger

THRESHOLD = 230


def start_char_detections(chart, title_pos, grouped, straightening, legend_bars_data=None, legend_position=None):
    """

    Args:
        chart:
        title_pos:
        grouped:
        straightening:
        legend_bars_data:
        legend_position:

    Returns:

    """
    image_edits.img_gray = cv2.cvtColor(chart, cv2.COLOR_BGR2GRAY)
    image_edits.img_color = chart

    try:
        image_edits.upscale()
    except Exception:
        logger.error("An error had occurred during image up-scaling, continue with original size")

    try:
        image_edits.thresholding(THRESHOLD)
    except Exception:
        logger.exception(
            "An error had occurred during image thresholding, can't continue the detection process")  # TODO exeption

    if straightening:
        try:
            # If the image straightening was successful, returns with the straightened image
            return image_edits.image_straightening()
        except Exception:
            logger.error("An error had occurred during image straightening, continue with original image")

    try:
        image_edits.get_bar_stats(legend_position)
    except Exception as e:
        logger.exception(
            "An error had occurred during bar stat extraction image, can't continue the detection process: %s", e)
        raise Exception("Hiba történt az oszlopok detektálása során, próbálja meg kiegyenesíteni a képet.")


    if grouped:
        logger.info("Start legend detections")
        try:
            legend_detections.detect_legend_position()
        except Exception as e:
            logger.error(str(e) + "todo") #TODO

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
        simple_bars_with_colors_array = color_detections.detect_colors(image_edits.img_color,
                                                                       image_edits.bars_stats,
                                                                       image_edits.bars_with_labels)
        color_detections.get_bar_color_for_simple_chart(simple_bars_with_colors_array)
        axis_detections.define_tick_type_for_axis(title_pos)
        image_detections.define_simple_chart_values(simple_bars_with_colors_array)
    to_latex.prepare_data_for_generation(image_detections.chart_type, legend_position, title_pos=title_pos)

    logger.info("Chart creation finished successfully")
