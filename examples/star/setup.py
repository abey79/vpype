from setuptools import setup

setup(
    name='star',
    version='0.1',
    py_modules=['star'],
    install_requires=[
        'vpype',
    ],
    entry_points='''
        [vpype.plugins]
        star=star.star:star
    ''',
)