"""
Setup and Packaging Configuration for Clara.

This module manages the installation, metadata specification, dependency
resolution, and configuration for the Clara backend package.

This uses Setuptools (https://setuptools.pypa.io/en/latest/) the standard
python mechanism for installing packages.
For the easiest installation just type the command (you'll probably need
root privileges for that):

    pip install -e .

"""

import os

from setuptools import find_packages, setup

PACKAGE_NAME = "clara"
VERSION = "0.1.0"
DESCRIPTION = "AI powered personal/work operating system for android"
AUTHOR = "Aryan Vishwakarma"
URL = "https://github.com/Aryan-202/clara-core.git"
LICENSE = "BSD 3-Clause License"

dir_setup = os.path.dirname(os.path.relpath(__file__))

setup(
    name=PACKAGE_NAME,
    version=VERSION,
    author=AUTHOR,
    url=URL,
    license=LICENSE,
    packages=find_packages(include=["clara*"]),
)
