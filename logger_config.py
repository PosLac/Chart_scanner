# import logging
# from colorlog import ColoredFormatter
#
#
# def setup_custom_logger():
#     logger = logging.getLogger('colored_logger')
#     logger.setLevel(logging.DEBUG)
#     stream_handler = logging.StreamHandler()
#     stream_handler.setLevel(logging.DEBUG)
#     formatter = ColoredFormatter(
#         "%(log_color)s%(asctime)s "
#         "%(log_color)s- "
#         "%(log_color)s%(levelname)-8s%(reset)s "
#         "%(log_color)s- "
#         "%(log_color)s%(message)s",
#         datefmt="%Y-%m-%d %H:%M:%S",
#         reset=True,
#         log_colors={
#             'DEBUG': 'white',
#             'INFO': 'white',
#             'WARNING': 'yellow',
#             'ERROR': 'red',
#         },
#         secondary_log_colors={}
#     )
#     stream_handler.setFormatter(formatter)
#     logger.addHandler(stream_handler)
#
#     return logger
