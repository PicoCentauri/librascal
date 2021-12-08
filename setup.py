import sys
import os
from os.path import join
from distutils.sysconfig import get_python_lib

from setuptools import find_packages
from skbuild import setup
from skbuild.constants import CMAKE_INSTALL_DIR
import re
from bindings.librascal import __version__

with open("AUTHORS.txt") as fp:
    author = ", ".join(fp.readlines()).replace("\n", "")

# read the version number from the library
#pattern = r"[0-9]\.[0-9]\.[0-9]"
#version = None
#with open("./bindings/librascal/__init__.py", "r") as fp:
#    for line in fp.readlines():
#        if "__version__" in line:
#            version = re.findall(pattern, line)[0]
#if version is None:
#    raise ValueError("Version number not found.")

with open("./requirements/minimal.txt", "r") as fp:
    requirements = list(filter(lambda x: "#" not in x, (line.strip() for line in fp)))

from pathlib import Path
this_directory = Path(__file__).parent
long_description = (this_directory / "README.rst").read_text()

with open('README.rst') as f:
    long_description = f.read()
#with open("./README.rst", "r") as fp:
#    description = ''.join(fp.readlines())

setup(
    name="librascal",
    version=__version__,
    long_description_content_type='text/x-rst',
    long_description=long_description,
    description="""A versatile and scalable computation of representations of \
    atomic structures for machine learning.""",
    author=author,
    license="LGPL-3.0-or-later",
    cmake_args=[
        "-DINSTALL_PATH:STRING=" + join(os.getcwd(), CMAKE_INSTALL_DIR()),
        "-DBUILD_EXAMPLES:BOOL=OFF",
    ],
    package_dir={"": "bindings"},
    packages=find_packages(where="bindings"),
    install_requires=requirements,
    # include_package_data=True,
    package_data={"": ["lib/librascal.*"]},
    zip_safe=False,
)
