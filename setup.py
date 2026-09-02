"""
Setup and Packaging Configuration for Clara.

This module manages the installation, metadata specification, dependency
resolution, and CLI entry-point configuration for the Clara backend package.

It acts as a standard setuptools-compatible setup script mirroring the
metadata and build configurations defined in `pyproject.toml`, ensuring seamless
compatibility for environments and workflows that do not natively utilize `uv`
or modern PEP 517/621-compliant build frontends.

This uses Setuptools (https://setuptools.pypa.io/en/latest/) the standard
python mechanism for installing packages.
For the easiest installation just type the command (you'll probably need
root privileges for that):

    pip install .

"""

import os
import sys
from pathlib import Path
from typing import List, Optional

from setuptools import find_packages, setup

PACKAGE_NAME = "clara"
VERSION = "0.1.0"
DESCRIPTION = "AI powered personal/work operating system for android"
AUTHOR = "Aryan Vishwakarma"
URL = "https://github.com/Aryan-202/clara-core.git"
LICENSE = "BSD 3-Clause License"

dir_setup = os.path.dirname(os.path.relpath(__file__))
class test_clara(Command):
    """Runs all the test under the clara/ folder
    """
    pass

