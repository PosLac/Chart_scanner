from setuptools import setup, find_packages

setup(
    name='Chart_scanner',
    version='1.0',
    packages=find_packages(),
    author='Pós László',
    description='A python app to convert raster images from charts to latex file',
    classifiers=[
        "Programming Language :: Python :: 3.9"
    ],
    install_requires=["pytesseract", "colorlog", "pylatex"]
)
