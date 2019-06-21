#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""

import os
import sys

os.chdir(os.path.dirname(os.path.abspath(__file__)))  # security

from setuptools import setup, find_packages

def read_file(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read().strip()


readme_filename = "README.rst"
if not os.path.exists("README.rst"):
    raise RuntimeError("%s not found, have you run generate_readme.py first?" % readme_filename)


classifiers = """\
Development Status :: 5 - Production/Stable
Intended Audience :: Developers
Intended Audience :: Information Technology
License :: OSI Approved :: MIT License
Natural Language :: English
Programming Language :: Python :: 2
Programming Language :: Python :: 2.7
Programming Language :: Python :: 3
Programming Language :: Python :: 3.4
Programming Language :: Python :: 3.5
Programming Language :: Python :: 3.6
Programming Language :: Python :: 3.7
Topic :: Software Development :: Libraries :: Python Modules
Operating System :: Microsoft :: Windows
Operating System :: Unix
Operating System :: MacOS :: MacOS X
"""


needs_pytest = {"pytest", "test", "ptr"}.intersection(sys.argv)
setup_requires = ["pytest-runner"] if needs_pytest else []

packages = find_packages(where="src")

setup(
    name="{{ cookiecutter.project_name }}",
    version=read_file("VERSION"),
    author="{{ cookiecutter.full_name.replace('\"', '\\\"') }}",
    author_email='{{ cookiecutter.email }}',
    url='https://github.com/pakal/compat-patcher',
    license="MIT",
    platforms=["any"],
    description="{{ cookiecutter.project_short_description }}",
    classifiers=filter(None, classifiers.split("\n")),
    long_description=read_file(readme_filename),
    package_dir={"": "src"},
    packages=packages,
    install_requires=["compat-patcher-core"],
    extras_require={},
    setup_requires=setup_requires,
    tests_require=[
        # Beware, keep in sync with tox.ini
        "pytest",
        "pytest-cov",
    ],
)
