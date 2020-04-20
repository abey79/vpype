from setuptools import setup


with open("README.md") as f:
    readme = f.read()

with open("LICENSE") as f:
    license = f.read()

setup(
    name="vpype",
    version="0.1.0",
    description="Vector pipeline for generative art",
    long_description=readme,
    long_description_content_type="text/markdown",
    author="Antoine Beyeler",
    url="https://github.com/abey79/vpype",
    license=license,
    packages=["vpype", "vpype_cli"],
    install_requires=[
        'click>=7.1',
        'click-plugins',
        'matplotlib',
        'scipy',  # scipy is needed to optimize svgpathtools' curve linearization
        'shapely[vectorized]',
        'svgwrite',
        'svgpathtools @ git+https://github.com/abey79/svgpathtools@vpype-fixes',
    ],
    entry_points='''
        [console_scripts]
        vpype=vpype_cli.cli:cli
    '''
)
