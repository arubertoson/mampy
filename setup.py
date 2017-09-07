#! /usr/bin/env mayapy

import os
import sys
from setuptools import setup, find_packages

if sys.version_info[:2] < (2, 7):
    sys.exit('mayalauncher requires Python 2.7 or higher.')

here = os.path.abspath(os.path.dirname(__file__))

# Get long description
try:
    import pypandoc
    pypandoc.convert_file('README.md', 'rst', outputfile='README.rst')
    with open('README.rst') as rst:
        description = rst.read()
    os.remove('README.rst')
except (IOError, ImportError):
    with open(os.path.join(here, 'README.md'), 'r') as f:
        description = f.read()

setup(
    name='mampy',
    version='0.2.1',
    description='Maya wrapper for the verbose Maya API',
    long_description=description,
    author='Marcus Albertsson',
    author_email='marcus.arubertoson@gmail.com',
    url='https://github.com/arubertoson/mampy',
    license='MIT',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'shiboken',
        'six',
        'sip',
        'Qt.py==1.1.0b1',
        'mvp',
        'contextlib2',
    ],
    classifiers=[
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        'Programming Language :: Python :: 2',
    ])
